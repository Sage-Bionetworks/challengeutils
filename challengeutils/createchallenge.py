'''What it does:
   ...
   
Input:  Challenge Project name
Output: The skeleton for two challenges site with initial wiki, two teams (admin and participants), 
        and a challenge wedget added on live site with a participant team associated with it. 

Example (run on bash): python challenge-skeleton.py myChallengeName

Code - Status: in progress
    TODO:
        1) try to create, then catch error if challenge or team exists
        3) add participants

Unit Testing:
'''
import json 
import synapseutils
import synapseclient
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
'''
A pre-defined wiki project is used as initial template for challenge sites.
To copy over the template synapseutils.copyWiki() function is used with template 
ID as source and new challenge project entity synID as destination.
'''
DREAM_CHALLENGE_TEMPLATE_SYNID = "syn2769515"

def create_evaluation_queue(syn, name, description, parentid):
    queue = syn.store(synapseclient.Evaluation(
      name=name,
      description=description,
      contentSource=parentid))
    logger.info("Created Queue %s(%s)" % (queue.name, queue.id))
    return(queue)

def create_team(syn, team_name, desc, privacy):
    team = syn.store(synapseclient.Team(name=team_name, description=desc, canPublicJoin=privacy))
    logger.info("Created Team %s(%s)" % (team.name, team.id))
    return(team.id)

def create_project(syn, project_name):
    project = synapseclient.Project(project_name)
    project = syn.store(project)
    logger.info("Created Project %s %s" % (project.id, project.name))
    return(project)

def create_live_page(syn, project, teamid):
    live_page_markdown = '## Banner\n\n\n**Pre-Registration Open:**\n**Launch:**\n**Close:**\n\n\n\n${jointeam?teamId=%s&isChallenge=true&isMemberMessage=You are Pre-registered&text=Pre-register&successMessage=Successfully joined&isSimpleRequestButton=true}\n> Number of Pre-registered Participants: ${teammembercount?teamId=%s} \n> Click [here](http://s3.amazonaws.com/geoloc.sagebase.org/%s.html) to see where in the world solvers are coming from. \n\n#### OVERVIEW - high level (same as DREAM website?) - for journalists, funders, and participants\n\n\n#### Challenge Organizers / Scientific Advisory Board:\n\n#### Data Contributors:\n\n#### Journal Partners:\n\n#### Funders and Sponsors:' % (teamid, teamid, teamid)
    syn.store(synapseclient.Wiki(title='', owner=project, markdown=live_page_markdown))

def create_challenge_widget(syn, project_live, team_part):
    project_live_id = synapseclient.utils.id_of(project_live)
    team_part_id = syn.getTeam(team_part)['id']

    challenge_object = {'id': u'1000', 'participantTeamId':team_part_id, 'projectId': project_live_id} 
    challenge = syn.restPOST('/challenge', json.dumps(challenge_object))
    challenge = syn.restGET('/entity/' + project_live_id + '/challenge')
    logger.info("Created Challenge id %s" % challenge['id'])
    return(challenge)

def update_wikipage_string(wikipage_string, challengeid, teamid, challenge_name, synid):
    wikipage_string = wikipage_string.replace("challengeId=0","challengeId=%s" % challengeid)
    wikipage_string = wikipage_string.replace("{teamId}", teamid)
    wikipage_string = wikipage_string.replace("teamId=0","teamId=%s" % teamid)
    wikipage_string = wikipage_string.replace("#!Map:0","#!Map:%s" % teamid)
    wikipage_string = wikipage_string.replace("{challengeName}", challenge_name)
    wikipage_string = wikipage_string.replace("projectId=syn0","projectId=%s" % synid)
    return(wikipage_string)

def createchallenge(syn, challenge_name, live_site):

    '''Create two project entity for challenge sites.
       1) live (public) and 2) staging (private until launch)
       Allow for users to set up the live site themselves
    '''
    if live_site is None:
        #live = challenge_name
        project_live = create_project(syn, challenge_name)
    else:
        project_live = syn.get(live_site)

    staging = challenge_name + ' - staging'
    project_staging = create_project(syn, staging)

    '''Create two teams for challenge sites.
       1) participant and 2) administrator
    '''
    team_part = challenge_name + ' Participants'
    team_admin = challenge_name + ' Admin'
    team_preReg = challenge_name + ' Preregistrants'

    team_part_id = create_team(syn, team_part, 'Challenge Particpant Team', privacy=True)
    team_admin_id = create_team(syn, team_admin, 'Challenge Admin Team', privacy=False)
    team_prereg_id = create_team(syn, team_preReg, 'Challenge Pre-registration Team', privacy=True)
    admin_perms = ['DOWNLOAD','DELETE','READ','CHANGE_PERMISSIONS','CHANGE_SETTINGS','CREATE','MODERATE','UPDATE']

    syn.setPermissions(project_staging, team_admin_id, admin_perms)
    syn.setPermissions(project_live, team_admin_id, admin_perms)

    if live_site is None:
        create_live_page(syn, project_live, team_prereg_id)

    # Copy challenge template, must pass in an id.  This is a bug in synu.copyWiki
    new_wikiids = synapseutils.copyWiki(syn, DREAM_CHALLENGE_TEMPLATE_SYNID, project_staging.id) 

    '''Create challenge widget on live challenge site with an associated participant team'''
    challenge = create_challenge_widget(syn, project_live, team_part)
    '''Create challenge final write up evaluation queue'''
    writeup_queue = create_evaluation_queue(syn, "%s Final Write-Up" % challenge_name, "Final Write up submission", project_live.id)
    for page in new_wikiids:
        wikipage = syn.getWiki(project_staging,page['id'])
        wikipage.markdown = update_wikipage_string(wikipage.markdown, challenge['id'], team_part_id, challenge_name, project_live.id)
        syn.store(wikipage)
