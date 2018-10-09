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

def _findAnnotation(annotations, key, annotType, isPrivate=False):
	if annotations.get(annotType) is not None:
		check = filter(lambda x: x.get('key') == key, annotations[annotType])
		if len(check) > 0:
			check[0]['isPrivate'] = isPrivate
	return(annotations)

def changeSubmissionAnnotationPrivacy(syn,evalID, annots, status='SCORED', isPrivate=False):
	"""
	annots: list of annotation keys to make public
	status: ALL, VALIDATED, INVALID, 
	"""
	status = None if status == 'ALL' else status
	bundle = syn.getSubmissionBundles(evalID,status=status)
	for (i,(item,status)) in enumerate(bundle):
		annotations = status.annotations
		for key in annots:
			annotations = _findAnnotation(annotations, key, "stringAnnos",isPrivate)
			annotations = _findAnnotation(annotations, key, "doubleAnnos",isPrivate)
			annotations = _findAnnotation(annotations, key, "longAnnos",isPrivate)
		status.annotations = annotations
		syn.store(status)
		#Checks if you have looped through all the submissions
		print(i)

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

def submissionToStatus(syn,submissionID,status='RECEIVED'):
	temp = syn.getSubmissionStatus(submissionID)
	temp.status = status
	syn.store(temp)

# Use syn.setPermissions
def changeACL(evaluationId, principalId):
	e = syn.getEvaluation(evaluationId)
	acl = syn._getACL(e)
	wanted = filter(lambda input: input.get('principalId', None) == principalId, acl['resourceAccess'])[0]
	## admin
	wanted['accessType'].append("READ_PRIVATE_SUBMISSION")
	syn._storeACL(e, acl)

def addSubmissionSynId(evaluationId):
	e = syn.getEvaluation(evaluationId)
	bundle = syn.getSubmissionBundles(e, status ="SCORED")
	for item,status in bundle:
		synId = {'isPrivate':False,'key':'synapseId','value':item.entityId}
		status.annotations['stringAnnos'].append(synId)
		syn.store(status)

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

def inviteMemberToTeam(team, user=None, email=None):
	"""
	Invite members to a team

	params: 
		team: Synapse Team id or name
		user: Synapse username or profile id
		email: Email of user, do not specify both email and user, but must specify one
	"""
	teamId = syn.getTeam(team)['id']
	isMember = False
	if email is None:
		userId = syn.getUserProfile(user)['ownerId']
		membershipStatus = syn.restGET("/team/%(teamId)s/member/%(individualId)s/membershipStatus" % dict(teamId=str(teamId), individualId=str(userId)))
		isMember = membershipStatus['isMember']
		invite = {'teamId': str(teamId), 'inviteeId': str(userId)}
	else:
		invite = {'teamId': str(teamId), 'inviteeEmail':str(email)}
	if not membershipStatus['isMember']:
		invite = syn.restPOST("/membershipInvitation", body=json.dumps(invite))


def createTeamWikis(challengeId):
	#challengeId = 4295
	#challengeId = 747
	registeredTeams = syn._GET_paginated("/challenge/%s/challengeTeam" % challengeId)
	for i in registeredTeams:
		submittedTeams = syn.tableQuery("SELECT * FROM syn17007653 where teamId = '%s'" % i['teamId'])
		if len(submittedTeams.asDataFrame()) == 0:
			team = syn.getTeam(i['teamId'])
			project = syn.store(synapseclient.Project("RAAD2 and Genentech %s" % team.name))
			wikiCopy = synu.copy(syn,"syn16984095",project.id)
			syn.store(synapseclient.Table("syn17007653",[[wikiCopy['syn16984095'],i['teamId']]]))

