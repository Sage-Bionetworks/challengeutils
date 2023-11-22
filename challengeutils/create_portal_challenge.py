"""Create challenge on the Sage Challenge Portal.

Feature to create a new challenge based on a template. The new challenge
will include tw Synapse projects (one for dev, one for prod), two teams
(Participants and Organizers), one table to list organizers, and an
evaluation queue.

Example::

    import challengeutils
    import synapseclient
    syn = synapseclient.login()
    challengeutils.create_portal_challenge.main(syn, "Foo Challenge")

"""
import logging
import sys

import synapseclient
from synapseclient.core.exceptions import SynapseHTTPError
import synapseutils

from . import challenge, permissions, utils

logger = logging.getLogger(__name__)

CHALLENGE_TEMPLATE_SYNID = "syn52941681"
TASK_WIKI_ID = "624554"
TABLE_TEMPLATE_SYNID = "syn52955244"
CHALLENGE_ROLES = ['organizer', 'contributor', 'sponsor']


def create_project(syn, project_name):
    """Creates Synapse Project

    Args:
        syn: Synpase object
        project_name: Name of project

    Returns:
        Project Entity
    """
    project = synapseclient.Project(project_name)
    project = syn.store(project)
    logger.info("Created Project {} ({})".format(project.name, project.id))
    return project



def create_evaluation_queue(syn, name, description, parentid):
    """
    Creates Evaluation Queues

    Args:
        syn: Synpase object
        name: Name of evaluation queue
        description: Description of queue
        parentid: Synapse project id

    Returns:
        Evalation Queue
    """
    queue_ent = synapseclient.Evaluation(
        name=name, description=description, contentSource=parentid
    )
    queue = syn.store(queue_ent)
    logger.info("Created Queue {}({})".format(queue.name, queue.id))
    return queue

def _create_live_wiki(syn, project):
    """Creates the wiki of the live challenge page

    Args:
        syn: Synpase object
        project: Synapse project
        teamid: Synapse team id of participant team
    """
    markdown = (
        syn
        .getWiki(CHALLENGE_TEMPLATE_SYNID)
        .get('markdown')
        .replace(
            "#!Synapse:syn52941681/tables/", 
            f"#!Synapse:{project.id}/tables/")
    )
    syn.store(synapseclient.Wiki(title="", owner=project, markdown=markdown))


def create_challenge_widget(syn, project_live, team_part_id):
    """Creates challenge widget - activates a Synapse project
    If challenge object exists, it retrieves existing object

    Args:
        syn: Synpase object
        project_live: Synapse id of live challenge project
        team_part_id: Synapse team id of participant team
    """
    try:
        chal_obj = challenge.create_challenge(syn, project_live, team_part_id)
        logger.info("Created Challenge ({})".format(chal_obj.id))
    except SynapseHTTPError:
        chal_obj = challenge.get_challenge(syn, project_live)
        logger.info("Fetched existing Challenge ({})".format(chal_obj.id))
    return chal_obj


def _update_wikipage_string(
    wikipage_string, challengeid, teamid, challenge_name, synid
):
    """Updates wikipage strings in the challenge wiki template
    with the newly created challengeid, teamid, challenge name and project id

    Args:
        wikipage_string: Original wikipage string
        challengeid: New challenge id
        teamid: Synapse Team id
        challenge_name: challenge name
        synid: Synapse id of project

    Returns:
        fixed wiki page string
    """
    wikipage_string = wikipage_string.replace(
        "challengeId=0", "challengeId=%s" % challengeid
    )
    wikipage_string = wikipage_string.replace("{teamId}", teamid)
    wikipage_string = wikipage_string.replace("teamId=0", "teamId=%s" % teamid)
    wikipage_string = wikipage_string.replace("#!Map:0", "#!Map:%s" % teamid)
    wikipage_string = wikipage_string.replace("{challengeName}", challenge_name)
    wikipage_string = wikipage_string.replace("projectId=syn0", "projectId=%s" % synid)
    return wikipage_string


def check_existing_and_delete_wiki(syn, synid):
    """Checks if wiki exists, and if so prompt to delete

    Args:
        syn: Synapse connection
        synid: Synapse id of an Entity
    """
    wiki = None
    try:
        wiki = syn.getWiki(synid)
    except SynapseHTTPError:
        pass

    if wiki is not None:
        logger.info("The staging project has already a wiki.")
        logger.info(wiki)
        user_input = (
            input("Do you agree to delete the wiki before continuing? (y/N) ") or "n"
        )
        if user_input.lower() not in ("y", "yes"):
            logger.info("Exiting")
            sys.exit(1)
        else:
            logger.info("Deleting wiki of the staging project ({})".format(wiki.id))
            syn.delete(wiki)


def main(syn, challenge_name, tasks_count, live_site=None):
    """Creates two project entity for challenge sites.
    1) live (public) and 2) staging (private until launch)
    Allow for users to set up the live site themselves

    Args:
        syn: Synapse object
        challenge_name: Name of the challenge
        live_site: If there is already a live site, specify live site Synapse
                   id. (Default is None)
        tasks_count: number of challenge tasks (default: 1)

    Returns:
        dict::

            {
                "live_projectid": projectid,
                "staging_projectid": projectid,
                "organizer_teamid": teams['team_org_id'],
                "participant_teamid": teams['team_part_id']
            }

    """
    # Create teams for challenge sites
    teams = _create_teams(syn, challenge_name)

    # Create live Project
    if live_site is None:
        project_live = create_project(syn, challenge_name)
        permissions.set_entity_permissions(
            syn, project_live, teams["team_org_id"], permission_level="moderate"
        )
        _create_live_wiki(syn, project_live)
    else:
        project_live = syn.get(live_site)

    challenge_obj = create_challenge_widget(syn, project_live, teams["team_part_id"])
    create_evaluation_queue(
        syn,
        "%s Project Submission" % challenge_name,
        "Project Submission",
        project_live.id,
    )
    create_organizer_tables(syn, project_live.id)
    create_data_folders(syn, project_live.id, tasks_count)

    # Create staging Project
    project_staging = create_project(syn, challenge_name + " - staging")
    permissions.set_entity_permissions(
        syn, project_staging, teams["team_org_id"], permission_level="edit"
    )
    # Checks if staging wiki exists, if so delete
    check_existing_and_delete_wiki(syn, project_staging.id)

    logger.info("Copying wiki template to {}".format(project_staging.name))
    new_wikiids = synapseutils.copyWiki(
        syn, CHALLENGE_TEMPLATE_SYNID, project_staging.id
    )
    for page in new_wikiids:
        wikipage = syn.getWiki(project_staging, page["id"])
        wikipage.markdown = _update_wikipage_string(
            wikipage.markdown,
            challenge_obj.id,
            teams["team_part_id"],
            challenge_name,
            project_live.id,
        )
        syn.store(wikipage)
    return {
        "live_projectid": project_live.id,
        "staging_projectid": project_staging.id,
        "admin_teamid": teams["team_admin_id"],
        "organizer_teamid": teams["team_org_id"],
        "participant_teamid": teams["team_part_id"],
        "preregistrantrant_teamid": teams["team_prereg_id"],
    }
