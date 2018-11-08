import os
import synapseclient
import pandas as pd
from synapseclient import Evaluation


def createEvaluationQueue(syn, name, description, status, parentId, submissionInstructionsMessage):
	queue = syn.store(Evaluation(
	  name=name,
	  description=description,
	  status=status,
	  contentSource=parentId,
	  submissionInstructionsMessage=submissionInstructionsMessage,
	  submissionReceiptMessage="Thanks for submitting to %s!" % name))
	return(queue)


def rescore(syn,evalID):
	bundle = syn.getSubmissionBundles(evalID,status='SCORED',limit=200)
	for (i,(item,status)) in enumerate(bundle):
		status.status = 'VALIDATED'
		syn.store(status)
		print(i)

# {u'firstRoundStart': u'2017-01-03T00:00:00.000Z',
#   u'numberOfRounds': 1,
#   u'roundDurationMillis': 3139200000,
#   u'submissionLimit': 6}
def setQuota(syn,evalID,quota=3):
	quota1 = dict(submissionLimit = quota)
	e = syn.getEvaluation(evalID)
	e.quota = quota1
	e = syn.store(e)

def reNameSubmissionFiles(syn,evalID,downloadLocation="./",stat="SCORED"):
	bundle = syn.getSubmissionBundles(evalID,status=stat,limit=200)
	for (i,(item,status)) in enumerate(bundle):
		if status.get("annotations") is not None:
			team = annots['stringAnnos'][0]['value']
		else:
			if item.get("teamId") is not None:
				team = syn.getTeam(item.get("teamId")).name
			else:
				user = syn.getUserProfile(item.userId).userName
		date = item.createdOn
		fileEnt = syn.getSubmission(item.id,downloadLocation=downloadLocation)
		fileName = os.path.basename(fileEnt.filePath)
		newName = team+"___"+date+"___"+fileName
		newName = newName.replace(' ','_')
		os.rename(fileName,newName)
		print(i)


def getEntityId(syn,evalID):
	bundle = syn.getSubmissionBundles(evalID,status='SCORED',limit=200)
	f = open('2.csv', 'w')
	f.write("team,email,public,wikiId,FileID,final,tiebreak,createdOn\n")
	for (i,(item,status)) in enumerate(bundle):
		annots = status.annotations
		#2
		#print(annots['doubleAnnos'][17])
		#print(annots['doubleAnnos'][-17])
		final = annots['doubleAnnos'][17]['value']
		tiebreak = annots['doubleAnnos'][-17]['value']
		#1A,B
		#tiebreak = annots['doubleAnnos'][-1]['value']
		#final = annots['doubleAnnos'][-3]['value']
		createdOn = item.createdOn
		user = syn.getUserProfile(item.userId)
		email = user.userName + "@synapse.org"
		try:
			synId = syn.get(item.entityId,downloadFile=False)
			synId = synId.parentId
			public = "True"
		except:
			synId = item.entityId
			public = "False"
		wiki = "https://www.synapse.org/#!Synapse:%s"%synId
		f.write("%s,%s,%s,%s,%s,%s,%s,%s\n" % (annots['stringAnnos'][0]['value'], email, public, wiki, item.entityId, final, tiebreak, createdOn))
	f.close()


# Use syn.setPermissions
def changeACL(evaluationId, principalId):
	e = syn.getEvaluation(evaluationId)
	acl = syn._getACL(e)
	wanted = filter(lambda input: input.get('principalId', None) == principalId, acl['resourceAccess'])[0]
	## admin
	wanted['accessType'].append("READ_PRIVATE_SUBMISSION")
	syn._storeACL(e, acl)

def getTeamStats(teamId):
	members = syn.getTeamMembers(teamId)
	info = []
	for i in members:
		user = syn.getUserProfile(i['member']['ownerId'])
		name = user['firstName'] + " " + user['lastName']
		if user.get("location") is not None:
			location = user['location']
		else:
			location = ""
		info.append([user['userName'],name,location,user['ownerId']])
	temp = pd.DataFrame(info,columns = ['username','name','location','userId'])
	temp['name'] = [i.encode('utf-8').decode('utf-8') for i in temp['name']]
	#temp.to_csv("challenge_stats.csv", index=False, encoding='utf-8')
	return(temp)

def numTeams(evalId):
	submissions = syn.getSubmissionBundles(evalId)
	allTeams = set()
	for sub, status in submissions:
		team = filter(lambda x: x.get('key') == "team", status.annotations['stringAnnos'])[0]
		allTeams.add(team['value'])
	print(len(allTeams))


def create_team_wikis(syn, synid, templateid, tracker_table_synid):
	"""
	Function that creates wiki pages from a template by looking at teams that
	are registered for a challenge.  The teams that have a wiki made for them
	Are stored into a trackerTable that has columns wikiSynId, and teamId

	params:
		synId: Synapse id of challenge project
		templateId:  Synapse id of the template
		trackerTableSynId: Synapse id of Table that tracks if wiki pages have been made per team
	"""
	

	challenge_ent = syn.get(synid)
	challenge_obj = getChallengeId(challenge_ent)
	registered_teams = syn._GET_paginated("/challenge/%s/challengeTeam" % challenge_obj['id'])
	for i in registered_teams:
		submitted_teams = syn.tableQuery("SELECT * FROM %s where teamId = '%s'" % (tracker_table_synid, i['teamId']))
		if len(submitted_teams.asDataFrame()) == 0:
			team = syn.getTeam(i['teamId'])
			#The project name is the challenge project name and team name
			project = syn.store(synapseclient.Project("%s %s" % (challenge_ent.name, team.name)))
			#Give admin access to the team
			syn.setPermissions(project, i['teamId'], accessType=['DELETE','CHANGE_SETTINGS','MODERATE','CREATE','READ','DOWNLOAD','UPDATE','CHANGE_PERMISSIONS'])
			wiki_copy = synu.copy(syn,templateid,project.id)
			#syn.sendMessage(i[])
			#Store copied synId to tracking table
			syn.store(synapseclient.Table(tracker_table_synid,[[wiki_copy[templateid],i['teamId']]]))

def set_entity_permissions(syn, entity, principalid=None, permission_level="view"):
	"""
	Convenience function to set ACL on an entity for a user or team based on
	permission levels (view, download...)

	params:
		entity: An Entity or Synapse ID to lookup
		principalid: Identifier of a user or group (defaults to PUBLIC users)
		permission_level: Can be "view","download","edit","edit_and_delete",or "admin"
	"""
	view = ["READ"]
	download = ['READ','DOWNLOAD']
	edit = ['DOWNLOAD', 'UPDATE', 'READ', 'CREATE']
	edit_and_delete = ['DOWNLOAD', 'UPDATE', 'READ', 'CREATE','DELETE']
	admin = ['DELETE','CHANGE_SETTINGS','MODERATE','CREATE','READ','DOWNLOAD','UPDATE','CHANGE_PERMISSIONS']
	permission_level_mapping = {'view':view,
								'download':download,
								'edit':edit,
								'edit_and_delete':'edit_and_delete',
								'admin':admin}
	assert permission_level in permission_level_mapping.keys()
	assert principalId is not None
	syn.setPermissions(entity, principalId=None, accessType=permission_level_mapping[permission_level])
