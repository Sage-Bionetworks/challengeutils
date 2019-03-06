'''What it does:
   ...

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
import json
import synapseutils
import synapseclient
import logging
import sys
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
'''
A pre-defined wiki project is used as initial template for challenge sites.
To copy over the template synapseutils.copyWiki() function is used with
template id as source and new challenge project entity synId as destination.
'''
DREAM_CHALLENGE_TEMPLATE_SYNID = "syn2769515"  # Template 1.0
# DREAM_CHALLENGE_TEMPLATE_SYNID = "syn18058986"  # Template 2.0


def create_project(syn, project_name):
    project = synapseclient.Project(project_name)
    # returns the handle to the project if the user has sufficient priviledge
    project = syn.store(project)
    logger.info('Created/Fetched Project %s (%s)' % (project.name, project.id))
    return(project)


def create_team(syn, team_name, desc, can_public_join):
    try:
        # raises a ValueError if a team does not exist
        team = syn.getTeam(team_name)
        print('The team %s already exists.' % team_name)
        print(team)
        user_input = input('Do you want to use this team? (Y/n) ') or 'y'
        if user_input.lower() not in ('y', 'yes'):
            logger.info('Please specify another team. Exiting.')
            sys.exit(1)
    except ValueError:
        team = synapseclient.Team(
            name=team_name, description=desc, canPublicJoin=can_public_join)
        # raises a ValueError if a team with this name already exists
        team = syn.store(team)
        logger.info('Created Team %s (%s)' % (team.name, team.id))
    return(team.id)


def create_evaluation_queue(syn, name, description, parentid):
    queue = syn.store(synapseclient.Evaluation(
        name=name,
        description=description,
        contentSource=parentid))
    logger.info('Created Queue %s(%s)' % (queue.name, queue.id))
    return(queue)


def create_live_page(syn, project, teamid):
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
    syn.store(synapseclient.Wiki(
        title='', owner=project, markdown=live_page_markdown))


def create_challenge_widget(syn, project_live, team_part_id):
    try:
        challenge = syn.restGET('/entity/' + project_live.id + '/challenge')
        logger.info("Fetched existing Challenge (%s)" % challenge['id'])
    except synapseclient.exceptions.SynapseError:
        challenge_object = {
            'id': u'1000', 'participantTeamId': team_part_id,
            'projectId': project_live.id}
        challenge = syn.restPOST('/challenge', json.dumps(challenge_object))
        challenge = syn.restGET('/entity/' + project_live.id + '/challenge')
        logger.info("Created Challenge (%s)" % challenge['id'])
    return(challenge)


def update_wikipage_string(
        wikipage_string, challengeid, teamid, challenge_name, synid):
    wikipage_string = wikipage_string.replace(
        'challengeId=0', 'challengeId=%s' % challengeid)
    wikipage_string = wikipage_string.replace('{teamId}', teamid)
    wikipage_string = wikipage_string.replace('teamId=0', 'teamId=%s' % teamid)
    wikipage_string = wikipage_string.replace('#!Map:0', '#!Map:%s' % teamid)
    wikipage_string = wikipage_string.replace(
        '{challengeName}', challenge_name)
    wikipage_string = wikipage_string.replace(
        'projectId=syn0', 'projectId=%s' % synid)
    return(wikipage_string)


def createchallenge(syn, challenge_name, live_site=None):
    '''
    Create two project entity for challenge sites.
    1) live (public) and 2) staging (private until launch)
    Allow for users to set up the live site themselves

    Args:
        syn: Synapse object
        challenge_name: Name of the challenge
        live_site: If there is already a live site, specify live site Synapse
                   id. (Default is None)

    Returns:
        Nothing
    '''
    if live_site is None:
        project_live = create_project(syn, challenge_name)
    else:
        project_live = syn.get(live_site)

    staging = challenge_name + ' - staging'
    project_staging = create_project(syn, staging)

    '''Create teams for challenge sites'''
    team_part = challenge_name + ' Participants'
    team_admin = challenge_name + ' Admin'
    team_preReg = challenge_name + ' Preregistrants'

    team_part_id = create_team(
        syn, team_part, 'Challenge Particpant Team', can_public_join=True)
    team_admin_id = create_team(
        syn, team_admin, 'Challenge Admin Team', can_public_join=False)
    team_prereg_id = create_team(
        syn, team_preReg, 'Challenge Pre-registration Team',
        can_public_join=True)

    admin_perms = ['DOWNLOAD', 'DELETE', 'READ', 'CHANGE_PERMISSIONS',
                   'CHANGE_SETTINGS', 'CREATE', 'MODERATE', 'UPDATE']
    syn.setPermissions(project_staging, team_admin_id, admin_perms)
    syn.setPermissions(project_live, team_admin_id, admin_perms)

    if live_site is None:
        create_live_page(syn, project_live, team_prereg_id)

    project_staging_wiki = None
    try:
        project_staging_wiki = syn.getWiki(project_staging.id)
    except Exception:
        pass

    if project_staging_wiki:
        print('The staging project has already a wiki.')
        print(project_staging_wiki)
        user_input = input(
            'Do you agree to delete the wiki before continuing? (y/N) ') or 'n'
        if user_input.lower() not in ('y', 'yes'):
            logger.info('Exiting')
            sys.exit(1)
        else:
            print('Deleting wiki of the staging project (%s)'
                  % project_staging_wiki.id)
            syn.delete(project_staging_wiki)

    logger.info('Copying wiki template to %s' % project_staging.name)
    new_wikiids = synapseutils.copyWiki(
        syn, DREAM_CHALLENGE_TEMPLATE_SYNID, project_staging.id)

    challenge = create_challenge_widget(syn, project_live, team_part_id)

    create_evaluation_queue(
        syn, '%s Final Write-Up' % challenge_name, 'Final Write-Up Submission',
        project_live.id)
    for page in new_wikiids:
        wikipage = syn.getWiki(project_staging, page['id'])
        wikipage.markdown = update_wikipage_string(
            wikipage.markdown, challenge['id'], team_part_id, challenge_name,
            project_live.id)
        syn.store(wikipage)
