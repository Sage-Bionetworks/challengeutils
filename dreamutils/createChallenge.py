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
import argparse
import getpass
from synapseclient import Entity, Project, Team, Wiki, Evaluation

def synapseLogin():
    try:
        syn = synapseclient.login()
    except Exception as e:
        print("Please provide your synapse username/email and password (You will only be prompted once)")
        Username = raw_input("Username: ")
        Password = getpass.getpass()
        syn = synapseclient.login(email=Username, password=Password,rememberMe=True)
    return(syn)

def createEvaluationQueue(syn, name, description, parentId):
    queue = syn.store(Evaluation(
      name=name,
      description=description,
      contentSource=parentId))
    return(queue)

def createTeam(syn, team_name, desc, privacy):
    team = syn.store(Team(name=team_name, description=desc, canPublicJoin=privacy))
    print("Created team %s(%s)" % (team.name, team.id))
    return(team.id)

def createProject(syn, project_name):
    project = Project(project_name)
    project = syn.store(project)
    print("Created project %s %s" % (project.id, project.name))
    return(project)

def copyChallengeWiki(syn, source_project_id, project):
    destination_project_id = synapseclient.utils.id_of(project)
    wikiIds = synapseutils.copyWiki(syn, source_project_id, destination_project_id) 
    return(wikiIds)

def createLivePage(syn, project, teamId):
    live_page_markdown = '## Banner\n\n\n**Pre-Registration Open:**\n**Launch:**\n**Close:**\n\n\n\n${jointeam?teamId=%s&isChallenge=true&isMemberMessage=You are Pre-registered&text=Pre-register&successMessage=Successfully joined&isSimpleRequestButton=true}\n> Number of Pre-registered Participants: ${teammembercount?teamId=%s} \n> Click [here](http://s3.amazonaws.com/geoloc.sagebase.org/%s.html) to see where in the world solvers are coming from. \n\n#### OVERVIEW - high level (same as DREAM website?) - for journalists, funders, and participants\n\n\n#### Challenge Organizers / Scientific Advisory Board:\n\n#### Data Contributors:\n\n#### Journal Partners:\n\n#### Funders and Sponsors:' % (teamId, teamId, teamId)
    syn.store(Wiki(title='', owner=project, markdown=live_page_markdown))

def createChallengeWidget(syn, project_live, team_part):
    project_live_id = synapseclient.utils.id_of(project_live)
    team_part_id = syn.getTeam(team_part)['id']

    challenge_object = {'id': u'1000', 'participantTeamId':team_part_id, 'projectId': project_live_id} 
    challenge = syn.restPOST('/challenge', json.dumps(challenge_object))
    challenge = syn.restGET('/entity/' + project_live_id + '/challenge')
    print("Created challenge id %s" % challenge['id'])
    return(challenge)

def updateValues(wikiPageString, challengeId, teamId, challengeName, synId):
    wikiPageString = wikiPageString.replace("{teamId}", teamId)
    wikiPageString = wikiPageString.replace("{challengeName}", challengeName)
    wikiPageString = wikiPageString.replace("teamId=0","teamId=%s" % teamId)
    wikiPageString = wikiPageString.replace("challengeId=0","challengeId=%s" % challengeId)
    wikiPageString = wikiPageString.replace("#!Map:0","#!Map:%s" % teamId)
    wikiPageString = wikiPageString.replace("projectId=syn0","projectId=%s" % synId)
    return(wikiPageString)

def main(challenge_name,live_site):

    '''Sage Bionetworks employee login
    '''
    syn = synapseLogin()

    '''Create two project entity for challenge sites.
       1) live (public) and 2) staging (private until launch)
       Allow for users to set up the live site themselves
    '''
    if live_site is not None:
        live = challenge_name
        project_live = createProject(syn, live)
    else:
        project_live = syn.get(live_site)

    staging = challenge_name + ' - staging'
    project_staging = createProject(syn, staging)

    '''Create two teams for challenge sites.
       1) participant and 2) administrator
    '''
    team_part = challenge_name + ' Participants'
    team_admin = challenge_name + ' Admin'
    team_preReg = challenge_name + ' Preregistrants'

    team_part_id = createTeam(syn, team_part, 'Challenge Particpant Team', privacy=True)
    team_admin_id = createTeam(syn, team_admin, 'Challenge Admin Team', privacy=False)
    team_preReg_id = createTeam(syn, team_preReg, 'Challenge Pre-registration Team', privacy=True)

    admin_perms = ['DOWNLOAD','DELETE','READ','CHANGE_PERMISSIONS','CHANGE_SETTINGS','CREATE','MODERATE','UPDATE']

    syn.setPermissions(project_staging, team_admin_id, admin_perms)
    syn.setPermissions(project_live, team_admin_id, admin_perms)

    '''A pre-defined wiki project is used as initial template for challenge sites.
       To copy over the template synapseutils.copyWiki() function is used with template 
       ID as source and new challenge project entity synID as destination.
    '''
    dream_challenge_template_id = 'syn2769515'
    
    if live_site is None:
        createLivePage(syn, project_live, team_preReg_id)

    newWikiIds = copyChallengeWiki(syn, dream_challenge_template_id, project_staging)

    '''Create challenge widget on live challenge site with an associated participant team'''
    challenge = createChallengeWidget(syn, project_live, team_part)
    '''Create challenge final write up evaluation queue'''
    writeUpQueue = createEvaluationQueue(syn, "%s Final Write-Up" % live, "Final Write up submission", project_live.id)
    for page in newWikiIds:
        wikiPage = syn.getWiki(project_staging,page['id'])
        wikiPage.markdown = updateValues(wikiPage.markdown, challenge['id'], team_part_id, live, project_live.id)
        syn.store(wikiPage)

def command_main(args):
    main(args.challengeName,args.liveSite)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("challengeName", help="Challenge name")
    parser.add_argument("--liveSite", help="Option to specify the live site synapse id when there is already a live site")
    args = parser.parse_args()
    command_main(args)




