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

#Get team locations
#Need to get participants before 2013
challenges= {"Whole-Cell Parameter Estimation":[2223721],#2013
			 "NIEHS-NCATS-UNC Toxicogenetics":[2223722,2223723], #2013
			 "HPN-DREAM Breast Cancer Network Inference":[2223724,2223725,2223726,2223728],#2013
			 "Rheumatoid Arthritis Responder":[2223744],#2014
			 "Alzheimer's Disease Big Data":[2223741],#2014
			 "Acute Myeloid Leukemia Outcome Prediction":[3320951],#2014
			 "Broad-DREAM Gene Essentiality Prediction":[3320895],#2014
			 "SMC-DNA":[2223743]#2014
			 "SMC-Het":[3328713], #2015
			 "DREAM Olfaction Prediction":[3323870], #2015
			 "Prostate Cancer":[3325264], #2015
			 "ALS Stratification Prize4Life":[3328255], #2015
			 "AstraZeneca-Sanger Drug Combination Prediction":[3329051], #2015
			 "SMC-DNA Meta":[3328707],#2015
			 "Respiratory Viral":[3332517],#2016
			 "Disease Module Identification":[3342189],#2016
			 "Somatic Mutation Calling":[2223743],#2016
			 "ENCODE":[3340988], #2016
			 "DREAM Idea Challenge":[3341755],#2016
			 "SMC-RNA":[3323365],#2016
			 "Digital Mammography":[3342365], #2016
			 "Multiple Myeloma":[3342899],#2017 preregister
			 "NCI-CPTAC Proteogenomics":[3351110], #2017 preregister
			 "Parkinsons Disease Digital Biomarker":[3354062] #2017 preregister
			}

teams = []
createdOn = []
allUsers = []
allLocations = []
for chal in challenges:
	print(chal)
	teams.append(','.join([str(i) for i in challenges[chal]]))
	team = syn.getTeam(challenges[chal][0])
	chal_users = set()
	chal_loc = []
	for i in challenges[chal]:
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
challenge_data['challenges'] = challenges.keys()
challenge_data['teams'] = teams
challenge_data['createdOn'] = createdOn
#Some of the dates are wrong
challenge_data['createdOn'][challenge_data['challenges'] == "Multiple Myeloma"] = 2017
challenge_data['createdOn'][challenge_data['challenges'] == "SMC-RNA"] = 2016
challenge_data['createdOn'][challenge_data['challenges'] == "SMC-DNA"] = 2016
challenge_data['createdOn'][challenge_data['challenges'] == "Alzheimer's Disease Big Data"] = 2014
challenge_data['createdOn'][challenge_data['challenges'] == "Rheumatoid Arthritis Responder"] = 2014
challenge_data['createdOn'][challenge_data['challenges'] == "DREAM Olfaction Prediction"] = 2015
challenge_data['createdOn'][challenge_data['challenges'] == "Respiratory Viral"] = 2016

challenge_data['users'] = allUsers
challenge_data['locations'] = allLocations

challenge_data.to_csv("challenge_stats.tsv",index=False, sep='\t',encoding='utf-8')



# for index,i in enumerate(challenge_data['challenges']):
# 	i = i.replace('DREAM','')
# 	i = i.replace('Challenge','')
# 	i = i.replace('challenge','')
# 	i = i.replace('1','')
# 	i = i.replace('  ',' ')
# 	print(i)
# 	challenge_data['challenges'][index] = i
