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

from . import challenge, permissions

logger = logging.getLogger(__name__)

PORTAL_TABLE = "syn51476218"
CHALLENGE_TEMPLATE_SYNID = "syn52941681"
TABLE_TEMPLATE_SYNID = "syn52955244"
CHALLENGE_ROLES = ["organizer", "contributor", "sponsor"]
TASK_WIKI_ID = "624554"


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
    logger.info(f" Project created: {project.name} ({project.id})")
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
        logger.info(f" Team {team_name} already exists.")
        logger.info(team)
        # If you press enter, this will default to 'y'
        user_input = input("Do you want to use this team? (Y/n) ") or "y"
        if user_input.lower() not in ("y", "yes"):
            logger.info(" Please specify a new challenge name. Exiting.")
            sys.exit(1)
    except ValueError:
        team = synapseclient.Team(
            name=team_name, description=desc, canPublicJoin=can_public_join
        )
        # raises a ValueError if a team with this name already exists
        team = syn.store(team)
        logger.info(f" Team created: {team.name} ({team.id})")
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
    queue_ent = synapseclient.Evaluation(
        name=name, description=description, contentSource=parentid
    )
    queue = syn.store(queue_ent)
    logger.info(f" Queue created: {queue.name} ({queue.id})")
    return queue


def _create_live_wiki(syn, project):
    """Creates the wiki of the live challenge page

    Args:
        syn: Synpase object
        project: Synapse project
        teamid: Synapse team id of participant team
    """
    markdown = """
<div align="center" class="alert alert-info">

###! More information coming soon!

</div>
    """
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
        logger.info(f" Acivated as Challenge (ID: {chal_obj.id})")
    except SynapseHTTPError:
        chal_obj = challenge.get_challenge(syn, project_live)
        logger.info(f" Fetched existing Challenge (ID: {chal_obj.id})")
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


def _create_teams(syn, challenge_name):
    """Create teams needed for a challenge: participants and organizers

    Args:
        syn: Synapse connection
        challenge_name: Name of the challenge

    Returns:
        dict of challenge team ids
    """
    team_part = challenge_name + " Participants"
    team_org = challenge_name + " Organizers"
    team_part_ent = create_team(
        syn, team_part, "Challenge Particpant Team", can_public_join=True
    )
    team_org_ent = create_team(
        syn, team_org, "Challenge Organizing Team", can_public_join=False
    )

    team_map = {
        "team_part_id": team_part_ent["id"],
        "team_org_id": team_org_ent["id"],
    }
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
        logger.info(" The staging project has already a wiki.")
        logger.info(wiki)
        user_input = (
            input("Do you agree to delete the wiki before continuing? (y/N) ") or "n"
        )
        if user_input.lower() not in ("y", "yes"):
            logger.info(" --- Exiting ---")
            sys.exit(1)
        else:
            logger.info(f" Deleting wiki of the staging project ({wiki.id})")
            syn.delete(wiki)


# FIXME: function does not work as expected, see inner comments for details.
def create_organizer_tables(syn, project_id):
    """Create main table of organizers and associating views.

    Args:
        syn: Synapse object
        parent_id: project synID
    """
    logger.info(" Creating tables...")
    view_ids = {}
    schema = synapseclient.Schema(
        name="Organizing Team",
        columns=syn.getColumns(TABLE_TEMPLATE_SYNID),
        parent=project_id,
    )
    table = synapseclient.Table(schema, [[]])

    # FIXME: for some reason, storing the table will then call on the
    #        `challengeutils` CLI again
    table = syn.store(table)
    logger.info(f"    Table created: {table.name} ({table.id}) ✔")

    # FIXME: due to the issue above, we are not able to create the
    #        MaterializedViews
    for role in CHALLENGE_ROLES:
        role_title = role.title() + "s"
        view = synapseclient.MaterializedViewSchema(
            name=role_title,
            parent=project_id,
            definingSQL=f"SELECT * FROM {table.id} WHERE challengeRole HAS ('{role}')",
        )
        view = syn.store(view)
        view_ids[role_title] = view.id
        logger.info(f"    MaterializedView created: {view.name} ({view.id}) ✔")
    return view_ids


def create_data_folders(syn, project_id, tasks_count):
    """Create folders for challenge data, one for each task.

    Args:
        syn: Synapse object
        parent_id: project synID
        tasks_count: Number of task folders to create
    """
    logger.info(" Creating folders...")
    folder_ids = {}
    for i in range(0, tasks_count):
        folder_name = f"Task {i + 1}"
        folder = synapseclient.Folder(name=folder_name, parent=project_id)
        folder = syn.store(folder)
        folder_ids[i] = folder.id
        logger.info(f"    Folder created: {folder.name} ({folder.id}) ✔")
    return folder_ids


def create_annotations(syn, project_id, table_ids, folder_ids):
    """Create annotations that will power the portal."""
    logger.info(" Creating basic annotations...")
    project = syn.get(project_id)

    # Set basic annotations to the project.
    for name, value in syn.get_annotations(CHALLENGE_TEMPLATE_SYNID).items():
        project[name] = ""

    # For annotations we do currently know, add their values.
    main_wiki_id = [
        wiki.get("id")
        for wiki in syn.getWikiHeaders(project_id)
        if not wiki.get("parentId")
    ][0]
    project["Overview"] = f"{project_id}/wiki/{main_wiki_id}"
    project["Abstract"] = "More challenge information coming soon!"
    # # for role, synid in table_ids.items():
    # #     annots[role] = synid
    for i, synid in folder_ids.items():
        project[f"Task_{i + 1}.DataFolder"] = synid
    project = syn.store(project)
    logger.info("    Annotations creation complete ✔")
    return project


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
    for i in range(0, tasks_count):
        create_evaluation_queue(
            syn,
            f"{challenge_name} Task {i + 1}",
            f"Task {i + 1} Submission",
            project_live.id,
        )
    # TODO: the following function does not work for some reason; see function
    #       for details
    # tables = create_organizer_tables(syn, project_live.id)
    tables = {}

    # Create data folder(s) and set their local sharing settings as:
    #     - organizers team = download access
    #     - participants team = download access
    folders = create_data_folders(syn, project_live.id, tasks_count)
    for _, folder_id in folders.items():
        permissions.set_entity_permissions(
            syn, folder_id, teams["team_org_id"], permission_level="download"
        )
        permissions.set_entity_permissions(
            syn, folder_id, teams["team_part_id"], permission_level="download"
        )

    # Add the basic annotations to the live Project - some can be pre-filled but the
    # majority will need to filled out on the web UI.
    project_live = create_annotations(syn, project_live.id, tables, folders)

    # Create staging Project
    project_staging = create_project(syn, challenge_name + " - staging")
    permissions.set_entity_permissions(
        syn, project_staging, teams["team_org_id"], permission_level="edit"
    )
    # Checks if staging wiki exists, if so delete
    check_existing_and_delete_wiki(syn, project_staging.id)

    logger.info(f" Copying wiki template to {project_staging.name}")
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

    # Create another Task tab per task.
    task_wikis = [
        wiki.get("title")
        for wiki in syn.getWikiHeaders(CHALLENGE_TEMPLATE_SYNID)
        if wiki.get("parentId") == TASK_WIKI_ID
    ]
    for i in range(1, tasks_count):
        new_task_tab = synapseclient.Wiki(
            title=f"Task {i + 1} (tab)",
            owner=project_staging.id,
            markdown="This page can be left empty - it will not appear on the portal.",
            parentWikiId=syn.getWiki(project_staging.id).id,
        )
        new_task_tab = syn.store(new_task_tab)
        for wiki_title in task_wikis:
            task_subwiki = synapseclient.Wiki(
                title=wiki_title,
                owner=project_staging.id,
                markdown="Refer to the Task 1 tab for examples",
                parentWikiId=new_task_tab.id,
            )
            syn.store(task_subwiki)

    # Add project to portal table.
    project_view = syn.get(PORTAL_TABLE)
    project_view.scopeIds.append(project_live.id)
    syn.store(project_view)
    logger.info(f" Challenge added to 'Curated Challenge Projects' ({PORTAL_TABLE})")

    return {
        "live_projectid": project_live.id,
        "staging_projectid": project_staging.id,
        "organizer_teamid": teams["team_org_id"],
        "participant_teamid": teams["team_part_id"],
    }
