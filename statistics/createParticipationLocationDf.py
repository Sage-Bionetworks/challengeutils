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

#CREATE participation.csv
challenges = {"6/4/2014":"syn312572",
			  "9/15/2014":"syn2384331",
			  "9/29/2014":"syn2455683",
			  "10/17/2014":"syn2290704",
			  "11/1/2014":"syn1734172",
			  "4/01/2015":"syn2811262",
			  "7/27/2015":"syn2813558",
			  "10/01/2015":"syn2873386",
		 	  "4/04/2016":"syn4231880"}
timeline = dict()
challengeName = dict()
for i in challenges:
	ent = syn.get(challenges[i])
	temp = syn.restGET('/entity/%s/challenge' % challenges[i])
	foo = syn.restGET('/challenge/%s/participant' % temp['id'])
	challengeName[i] = ent.name
	timeline[i] = foo['totalNumberOfResults']

#HPN-DREAM breast cancer network inference challenge
teams = [2223724,2223725,2223726,2223727,2223728]
timeline["03/01/2013"] = len(getUniqMembers(teams))
challengeName["03/01/2013"] = "HPN-DREAM breast cancer network inference challenge"

#NIEHS-NCATS-UNC DREAM Toxicogenetics Challenge
teams = [2223722,2223723]
timeline["02/01/2013"] = len(getUniqMembers(teams))
challengeName["02/01/2013"] = "NIEHS-NCATS-UNC DREAM Toxicogenetics Challenge"

#The Whole-Cell Parameter Estimation DREAM Challenge
teams = [2223721]
timeline["01/01/2013"] = len(getUniqMembers(teams))
challengeName["01/01/2013"] = "The Whole-Cell Parameter Estimation DREAM Challenge"

for index,i in enumerate(participation['Name']):
    i = i.replace('DREAM','')
    i = i.replace('Challenge','')
    i = i.replace('challenge','')
    i = i.replace('1','')
    i = i.replace('  ',' ')
    participation['Name'][index] = i

participation = pd.DataFrame(timeline.values(), index= timeline.keys(),columns = ["Number"])
participation['newDate'] = [calendar.timegm(time.strptime(i,"%m/%d/%Y")) for i in participation.index]
participation['Year'] = [time.strptime(i,"%m/%d/%Y")[0] for i in participation.index]
participation['Name'] = challengeName.values()
participation = participation.sort_values("newDate",ascending=False)

#Create challenge_locations.txt
#Get list of unique members
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
teams = [2223721, #Whole-Cell Parameter Estimation
		 2223722, #NIEHS-NCATS-UNC 1
		 2223723, #NIEHS-NCATS-UNC 2
		 2223724, #HPN-DREAM 1A
		 2223725, #HPN-DREAM 1B
		 2223726, #HPN-DREAM 2A Experimental timecourse prediction
		 2223727, #HPN-DREAM 2B
		 2223728, #HPN-DREAM 3
		 2223743, #SMC-mutation
		 2223744, #RA responder challenge
		 3320895, #Broad gene essentiality
		 3320951, #AML
		 3332517, #RA viral challenge
		 3323365, #SMCRNA
		 3323870, #Olfaction
		 3325264, #Prostate challenge
		 3328255, #ALS challenge
		 3328707, #SMC-DNA Meta
		 3328713, #SMC-Het
		 3329051, #AZ
		 3342365, #DM challenge
		 3340988, #ENCODE
		 3341755, #Idea challenge
		 3342189, #Disease Module Identification DREAM Challenge
		 3342899 #MM preregister
		 ]
allMembers = getUniqMemberCount(teams)
createChallengeLocationList(allMembers,"challenge_locations.txt")
