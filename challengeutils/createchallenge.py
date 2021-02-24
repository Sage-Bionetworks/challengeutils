"""The skeleton for two challenges site with initial wiki, four teams
(admin, participants, organizers, and preregistrants), and
a challenge widget added on live site with a participant
team associated with it.

For more information on challenges administration:
https://docs.synapse.org/articles/challenge_administration.html

Example::

    import challengeutils
    import synapseclient
    syn = synapseclient.login()
    challengeutils.createchallenge.main(syn, "Plouf Challenge")

"""
import logging
import sys

import synapseclient
from synapseclient.core.exceptions import SynapseHTTPError
import synapseutils

from . import challenge, permissions, utils

logger = logging.getLogger(__name__)

# TODO: Add participants
# A pre-defined wiki project is used as initial template for challenge sites.
# To copy over the template synapseutils.copyWiki() function is used with
# template id as source and new challenge project entity synId as destination.
# DREAM_CHALLENGE_TEMPLATE_SYNID = "syn2769515"  # Template 1.0
DREAM_CHALLENGE_TEMPLATE_SYNID = "syn18058986"  # Template 2.0

LIVE_PAGE_MARKDOWN = (
    '## Banner\n\n'
    '{row}\n {column width=2}\n '
    '{column}\n {column width=4}\n'
    '#### ${jointeam?teamId=%s&isChallenge=false&isMemberMessage=You have successfully preregistered for the challenge&text=Click here to preregister&isSimpleRequestButton=true&requestOpenText=Your registration is in progress&successMessage=Your registration is in progress}\n '
    '{column}\n {column width=5}\n'
    '###! There are ${teammembercount?teamId=%s} preregistered participants. <br>**Join them now!**\n '
    '{column}\n {column width=1}\n '
    '{column}\n{row}\n'
    '\n---\n\n'
    '## Overview\n\n<font size=4>**Goal:**</font>\n\n<font size=4>**Motivation:**</font>\n'
    '\n---\n\n'
    '## Timeline\n\n'
    '\n---\n\n'
    '## Challenge Organizers\n\n'
    '\n---\n\n'
    '## Funders/Sponsors/Data Contributors/Journal Partners:\n\n'
)


def create_project(syn, project_name):
    """Creates Synapse Project

    Args:
        syn: Synpase object
        project_name: Name of project

    Returns:
        Project Entity
    """
    project = synapseclient.Project(project_name)
    # returns the handle to the project if the user has sufficient priviledge
    project = syn.store(project)
    logger.info('Created/Fetched Project {} ({})'.format(project.name,
                                                         project.id))
    return project


def create_team(syn, team_name, desc, can_public_join=False):
    """Creates Synapse Team

    Args:
        syn: Synpase object
        team_name: Name of team
        desc: Description of team
        can_public_join: true for teams which members can join without
                         an invitation or approval. Default to False

    Returns:
        Synapse Team id
    """
    try:
        # raises a ValueError if a team does not exist
        team = syn.getTeam(team_name)
        logger.info('The team {} already exists.'.format(team_name))
        logger.info(team)
        # If you press enter, this will default to 'y'
        user_input = input('Do you want to use this team? (Y/n) ') or 'y'
        if user_input.lower() not in ('y', 'yes'):
            logger.info('Please specify a new challenge name. Exiting.')
            sys.exit(1)
    except ValueError:
        team = synapseclient.Team(name=team_name,
                                  description=desc,
                                  canPublicJoin=can_public_join)
        # raises a ValueError if a team with this name already exists
        team = syn.store(team)
        logger.info('Created Team {} ({})'.format(team.name, team.id))
    return team


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
    queue_ent = synapseclient.Evaluation(name=name,
                                         description=description,
                                         contentSource=parentid)
    queue = syn.store(queue_ent)
    logger.info('Created Queue {}({})'.format(queue.name, queue.id))
    return queue


def _create_live_wiki(syn, project, teamid):
    """Creates the wiki of the live challenge page

    Args:
        syn: Synpase object
        project: Synapse project
        teamid: Synapse team id of participant team
    """
    markdown = LIVE_PAGE_MARKDOWN % (teamid, teamid)
    syn.store(synapseclient.Wiki(title='', owner=project,
                                 markdown=markdown))


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


def _update_wikipage_string(wikipage_string, challengeid, teamid,
                            challenge_name, synid):
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
    wikipage_string = wikipage_string.replace('challengeId=0',
                                              'challengeId=%s' % challengeid)
    wikipage_string = wikipage_string.replace('{teamId}', teamid)
    wikipage_string = wikipage_string.replace('teamId=0',
                                              'teamId=%s' % teamid)
    wikipage_string = wikipage_string.replace('#!Map:0', '#!Map:%s' % teamid)
    wikipage_string = wikipage_string.replace('{challengeName}',
                                              challenge_name)
    wikipage_string = wikipage_string.replace('projectId=syn0',
                                              'projectId=%s' % synid)
    return wikipage_string


def _create_teams(syn, challenge_name):
    """Create teams needed for a challenge: participant, admin, organizer, and
    preregistration team

    Args:
        syn: Synapse connection
        challenge_name: Name of the challenge

    Returns:
        dict of challenge team ids
    """
    team_part = challenge_name + ' Participants'
    team_admin = challenge_name + ' Admin'
    team_prereg = challenge_name + ' Preregistrants'
    # The organizer team is used to gate permissions
    # The motivation is that not everyone needs admin access to the projects
    team_org = challenge_name + ' Organizers'
    team_part_ent = create_team(syn, team_part, 'Challenge Particpant Team',
                                can_public_join=True)
    team_admin_ent = create_team(syn, team_admin, 'Challenge Admin Team',
                                 can_public_join=False)
    team_org_ent = create_team(syn, team_org, 'Challenge Organizing Team',
                               can_public_join=False)
    team_prereg_ent = create_team(syn, team_prereg,
                                  'Challenge Pre-registration Team',
                                  can_public_join=True)

    team_map = {'team_part_id': team_part_ent['id'],
                'team_admin_id': team_admin_ent['id'],
                'team_prereg_id': team_prereg_ent['id'],
                'team_org_id': team_org_ent['id']}
    return team_map


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
        logger.info('The staging project has already a wiki.')
        logger.info(wiki)
        user_input = input(
            'Do you agree to delete the wiki before continuing? (y/N) ') or 'n'
        if user_input.lower() not in ('y', 'yes'):
            logger.info('Exiting')
            sys.exit(1)
        else:
            logger.info('Deleting wiki of the staging project ({})'.format(
                wiki.id))
            syn.delete(wiki)


def main(syn, challenge_name, live_site=None):
    """Creates two project entity for challenge sites.
    1) live (public) and 2) staging (private until launch)
    Allow for users to set up the live site themselves

    Args:
        syn: Synapse object
        challenge_name: Name of the challenge
        live_site: If there is already a live site, specify live site Synapse
                   id. (Default is None)

    Returns:
        dict::

            {
                "live_projectid": projectid,
                "staging_projectid": projectid,
                "admin_teamid": teams['team_admin_id'],
                "organizer_teamid": teams['team_org_id'],
                "participant_teamid": teams['team_part_id'],
                "preregistrantrant_teamid": teams['team_prereg_id']
            }

    """
    # Create teams for challenge sites
    teams = _create_teams(syn, challenge_name)

    # Create live Project
    if live_site is None:
        project_live = create_project(syn, challenge_name)
        permissions.set_entity_permissions(syn, project_live,
                                           teams['team_admin_id'],
                                           permission_level="admin")
        permissions.set_entity_permissions(syn, project_live,
                                           teams['team_org_id'],
                                           permission_level="download")
        _create_live_wiki(syn, project_live, teams['team_prereg_id'])
    else:
        project_live = syn.get(live_site)

    challenge_obj = create_challenge_widget(syn, project_live,
                                            teams['team_part_id'])
    create_evaluation_queue(syn, '%s Project Submission' % challenge_name,
                            'Project Submission',
                            project_live.id)

    # Create staging Project
    project_staging = create_project(syn, challenge_name + ' - staging')
    permissions.set_entity_permissions(syn, project_staging,
                                       teams['team_admin_id'],
                                       permission_level="admin")
    permissions.set_entity_permissions(syn, project_staging,
                                       teams['team_org_id'],
                                       permission_level="edit")
    # Checks if staging wiki exists, if so delete
    check_existing_and_delete_wiki(syn, project_staging.id)

    logger.info('Copying wiki template to {}'.format(project_staging.name))
    new_wikiids = synapseutils.copyWiki(syn, DREAM_CHALLENGE_TEMPLATE_SYNID,
                                        project_staging.id)
    for page in new_wikiids:
        wikipage = syn.getWiki(project_staging, page['id'])
        wikipage.markdown = _update_wikipage_string(wikipage.markdown,
                                                    challenge_obj.id,
                                                    teams['team_part_id'],
                                                    challenge_name,
                                                    project_live.id)
        syn.store(wikipage)
    return {"live_projectid": project_live.id,
            "staging_projectid": project_staging.id,
            "admin_teamid": teams['team_admin_id'],
            "organizer_teamid": teams['team_org_id'],
            "participant_teamid": teams['team_part_id'],
            "preregistrantrant_teamid": teams['team_prereg_id']}
