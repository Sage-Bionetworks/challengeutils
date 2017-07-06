import synapseclient
import pandas as pd
import calendar
import time
syn = synapseclient.login()

def getUniqMembers(listOfTeams):
	"""
	:param listOfTeams:  Takes a list of teams
	"""
	allmembers= set()
	for i in teams:
		members = syn.getTeamMembers(i)
		for member in members:
			members.add(member['member']['ownerId'])
	return(members)

#Create challenge locations
def createChallengeLocationList(allMembers,locationFileName):
	locations = []
	for member in allMembers:
		user = syn.getUserProfile(member)
		loc = user.get('location',None)
		if loc is not None and loc != '':
			locations.append(loc)
	with open(locationFileName,'w+') as location_doc:
		location_doc.write('locations\n')
		for i in locations:
			location_doc.write(i.encode('utf-8') + "\n")

#EDIT syn10163902 TO ADD CHALLENGES
challengesTable = syn.tableQuery('select * from syn10163902')
challengesTableDf = challengesTable.asDataFrame()

teams = []
createdOn = []
allUsers = []
allLocations = []
for chal in challengesTableDf['challenge']:
	print(chal)
	chalTeams = challengesTableDf['teams'][challengesTableDf['challenge'] == chal].values[0]
	teams.append(chalTeams)
	allTeams =chalTeams.split(",")
	team = syn.getTeam(allTeams[0])
	chal_users = set()
	chal_loc = []
	for i in allTeams:
		for member in syn.getTeamMembers(i):
			chal_users.add(member['member']['userName'])
			member = syn.getUserProfile(member['member']['ownerId'])
			loc = member.get('location',None)
			if loc is not None and loc != '':
				chal_loc.append(loc)
	createdOn.append(team.createdOn.split("-")[0])
	allUsers.append(",".join(chal_users))
	allLocations.append("|".join(chal_loc))

challenge_data = pd.DataFrame()
challenge_data['challenges'] = challengesTableDf['challenge']
challenge_data['teams'] = teams
challenge_data['createdOn'] = createdOn
#Some of the dates are wrong
challenge_data['createdOn'][challenge_data['challenges'] == "Multiple Myeloma"] = 2017
challenge_data['createdOn'][challenge_data['challenges'] == "SMC-RNA"] = 2016
challenge_data['createdOn'][challenge_data['challenges'] == "SMC-DNA Meta"] = 2015
challenge_data['createdOn'][challenge_data['challenges'] == "SMC-DNA"] = 2014
challenge_data['createdOn'][challenge_data['challenges'] == "Alzheimer's Disease Big Data"] = 2014
challenge_data['createdOn'][challenge_data['challenges'] == "Rheumatoid Arthritis Responder"] = 2014
challenge_data['createdOn'][challenge_data['challenges'] == "DREAM Olfaction Prediction"] = 2015
challenge_data['createdOn'][challenge_data['challenges'] == "Respiratory Viral"] = 2016

challenge_data['users'] = allUsers
challenge_data['locations'] = allLocations
challenge_data.to_csv("challenge_stats.tsv",index=False, sep='\t',encoding='utf-8')