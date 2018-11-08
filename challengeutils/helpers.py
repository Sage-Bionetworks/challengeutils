import os
import synapseclient

def rename_submission_files(syn, evaluationid, download_location="./", status="SCORED"):
	'''
	This function renames the submission files of an evaluation queue.  For many challenges we require
	participants to submit files that are named one thing such as prediction.csv.
	This function renames them to

	submitter_date_filename

	params:
		syn: synapse object
		evaluationid:  Id of Evaluation queue
		download_location:  location to download files to (Default is ./)
		status: The submissions to download (Default is SCORED)
	'''
	submission_bundle = syn.getSubmissionBundles(evaluationid, status=status)
	for sub, status in submission_bundle:
		if sub.get("teamId") is not None:
			submitter = syn.getTeam(sub.get("teamId"))['name']
		else:
			submitter = syn.getUserProfile(sub.userId)['userName']
		date = sub.createdOn
		submission_ent = syn.getSubmission(sub.id,downloadLocation=download_location)
		filename = os.path.basename(submission_ent.filePath)
		newname = submitter+"___"+date+"___"+filename
		newname = newname.replace(' ','_')
		os.rename(filename,newname)
		print(newname)


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
