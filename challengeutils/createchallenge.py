'''
Creates challenge space in Synapse

Input:  Challenge Project name
Output: The skeleton for two challenges site with initial wiki, three teams
        (admin, participants, and  preregistrants), and a challenge widget
        added on live site with a participant team associated with it.

Example (run on bash): challengeutils createchallenge "Plouf Challenge"

Code - Status: in progress
    TODO:
        1) add participants?

Unit Testing:
'''
import logging
import json
import sys

import synapseclient
from synapseclient.exceptions import SynapseHTTPError
import synapseutils

from .synapse import Synapse
from . import permissions

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)
'''
A pre-defined wiki project is used as initial template for challenge sites.
To copy over the template synapseutils.copyWiki() function is used with
template id as source and new challenge project entity synId as destination.
'''
# DREAM_CHALLENGE_TEMPLATE_SYNID = "syn2769515"  # Template 1.0
DREAM_CHALLENGE_TEMPLATE_SYNID = "syn18058986"  # Template 2.0


def create_project(project_name):
    '''
    Convenience function to create Synapse Project

    Args:
        project_name: Name of project

    Returns:
        Project Entity
    '''
    syn = Synapse().client()
    project = synapseclient.Project(project_name)
    # returns the handle to the project if the user has sufficient priviledge
    project = syn.store(project)
    LOGGER.info(f'Created/Fetched Project {project.name} ({project.id})')
    return project


def create_team(team_name, desc, can_public_join=False):
    '''
    Convenience function to create Synapse Team

    Args:
        syn: Synpase object
        team_name: Name of team
        desc: Description of team
        can_public_join: true for teams which members can join without
                         an invitation or approval. Default to False

    Returns:
        Synapse Team id
    '''
    syn = Synapse().client()
    try:
        # raises a ValueError if a team does not exist
        team = syn.getTeam(team_name)
        LOGGER.info(f'The team {team_name} already exists.')
        LOGGER.info(team)
        user_input = input('Do you want to use this team? (Y/n) ') or 'y'
        if user_input.lower() not in ('y', 'yes'):
            LOGGER.info('Please specify another team. Exiting.')
            sys.exit(1)
    except ValueError:
        team = synapseclient.Team(
            name=team_name, description=desc, canPublicJoin=can_public_join)
        # raises a ValueError if a team with this name already exists
        team = syn.store(team)
        LOGGER.info(f'Created Team {team.name} ({team.id})')
    return team.id


def create_evaluation_queue(name, description, parentid):
    '''
    Convenience function to create Evaluation Queues

    Args:
        syn: Synpase object
        name: Name of evaluation queue
        description: Description of queue
        parentid: Synapse project id

    Returns:
        Evalation Queue
    '''
    syn = Synapse().client()
    queue = syn.store(synapseclient.Evaluation(name=name,
                                               description=description,
                                               contentSource=parentid))
    LOGGER.info(f'Created Queue {queue.name}({queue.id})')
    return queue


def create_live_page(project, teamid):
    '''
    Create the wiki of the live challenge page

    Args:
        syn: Synpase object
        project: Synapse project
        teamid: Synapse team id of participant team
    '''
    syn = Synapse().client()
    live_page_markdown = (
        '## Banner\n\n\n'
        '**Pre-Registration Open:**\n'
        '**Launch:**\n'
        '**Close:**\n\n\n\n'
        '${jointeam?teamId=%s&isChallenge=true&isMemberMessage=You are '
        'Pre-registered&text=Pre-register&successMessage='
        'Successfully joined&isSimpleRequestButton=true}\n> Number of Pre-'
        'registered Participants: ${teammembercount?teamId=%s}\n> Click [here]'
        '(http://s3.amazonaws.com/geoloc.sagebase.org/%s.html) to see where '
        'in the world solvers are coming from. \n\n'
        '#### OVERVIEW - high level (same as DREAM website?) - for '
        'journalists, funders, and participants\n\n\n'
        '#### Challenge Organizers / Scientific Advisory Board:\n\n'
        '#### Data Contributors:\n\n'
        '#### Journal Partners:\n\n'
        '#### Funders and Sponsors:') % (teamid, teamid, teamid)
    syn.store(synapseclient.Wiki(title='', owner=project,
                                 markdown=live_page_markdown))


def create_challenge_widget(project_live, team_part_id):
    '''
    Create challenge widget - activates a Synapse project

    Args:
        syn: Synpase object
        project_live: Synapse id of live challenge project
        team_part_id: Synapse team id of participant team
    '''
    syn = Synapse().client()
    try:
        challenge = syn.restGET(f'/entity/{project_live.id}/challenge')
        LOGGER.info(f"Fetched existing Challenge ({challenge['id']})")
    except synapseclient.exceptions.SynapseError:
        challenge_object = {'id': u'1000', 'participantTeamId': team_part_id,
                            'projectId': project_live.id}
        challenge = syn.restPOST('/challenge', json.dumps(challenge_object))
        challenge = syn.restGET(f'/entity/{project_live.id}/challenge')
        LOGGER.info(f"Created Challenge ({challenge['id']})")
    return challenge


def update_wikipage_string(wikipage_string, challengeid, teamid,
                           challenge_name, synid):
    '''
    Helper function to update wikipage strings in the challenge wiki template
    with the newly created challengeid, teamid, challenge name and project id

    Args:
        wikipage_string: Original wikipage string
        challengeid: New challenge id
        teamid: Synapse Team id
        challenge_name: challenge name
        synid: Synapse id of project

    Returns:
        fixed wiki page string
    '''
    wikipage_string = wikipage_string.replace('challengeId=0',
                                              f'challengeId={challengeid}')
    wikipage_string = wikipage_string.replace('{teamId}', teamid)
    wikipage_string = wikipage_string.replace('teamId=0', f'teamId={teamid}')
    wikipage_string = wikipage_string.replace('#!Map:0', f'#!Map:{teamid}')
    wikipage_string = wikipage_string.replace('{challengeName}',
                                              challenge_name)
    wikipage_string = wikipage_string.replace('projectId=syn0',
                                              f'projectId={synid}')
    return wikipage_string


def createchallenge(challenge_name, live_site=None):
    '''
    Create two project entity for challenge sites.
    1) live (public) and 2) staging (private until launch)
    Allow for users to set up the live site themselves

    Args:
        syn: Synapse object
        challenge_name: Name of the challenge
        live_site: If there is already a live site, specify live site Synapse
                   id. (Default is None)
    '''
    syn = Synapse().client()
    if live_site is None:
        project_live = create_project(challenge_name)
    else:
        project_live = syn.get(live_site)

    staging = challenge_name + ' - staging'
    project_staging = create_project(staging)

    # Create teams for challenge sites
    team_part = challenge_name + ' Participants'
    team_admin = challenge_name + ' Admin'
    team_prereg = challenge_name + ' Preregistrants'

    team_part_id = create_team(team_part, 'Challenge Particpant Team',
                               can_public_join=True)
    team_admin_id = create_team(team_admin, 'Challenge Admin Team',
                                can_public_join=False)
    team_prereg_id = create_team(team_prereg,
                                 'Challenge Pre-registration Team',
                                 can_public_join=True)

    permissions.set_entity_permissions(syn, project_staging, team_admin_id,
                                       permission_level="admin")
    permissions.set_entity_permissions(syn, project_live, team_admin_id,
                                       permission_level="admin")
    if live_site is None:
        create_live_page(project_live, team_prereg_id)

    project_staging_wiki = None
    # If entity doesn't have a wiki, an error will be thrown
    try:
        project_staging_wiki = syn.getWiki(project_staging.id)
    except SynapseHTTPError:
        pass

    if project_staging_wiki:
        LOGGER.info('The staging project has already a wiki.')
        LOGGER.info(project_staging_wiki)
        user_input = input('Do you agree to delete the wiki before '
                           'continuing? (y/N) ') or 'n'
        if user_input.lower() not in ('y', 'yes'):
            LOGGER.info('Exiting')
            sys.exit(1)
        else:
            LOGGER.info('Deleting wiki of the staging project '
                        f'({project_staging_wiki.id})')
            syn.delete(project_staging_wiki)

    LOGGER.info(f'Copying wiki template to {project_staging.name}')
    new_wikiids = synapseutils.copyWiki(syn, DREAM_CHALLENGE_TEMPLATE_SYNID,
                                        project_staging.id)

    challenge = create_challenge_widget(project_live, team_part_id)

    create_evaluation_queue(f'{challenge_name} Final Write-Up',
                            'Final Write-Up Submission',
                            project_live.id)
    for page in new_wikiids:
        wikipage = syn.getWiki(project_staging, page['id'])
        wikipage.markdown = update_wikipage_string(wikipage.markdown,
                                                   challenge['id'],
                                                   team_part_id,
                                                   challenge_name,
                                                   project_live.id)
        syn.store(wikipage)
