# Script to download statistics 3 docker challenges, Proteogenomics, MM, DM
# number of models
# round
# sc
# runtime
# success or invalid
# team
import synapseclient
import pandas as pd
import datetime
import math
syn = synapseclient.login()

def createDockerSubmissionStats(evalId, roundStart, roundEnd, roundValue, subCh, challenge):
	subBundle = syn.getSubmissionBundles(evalId)
	submissions = pd.DataFrame()
	for sub, status in subBundle:
		timeSubmit = synapseclient.utils.to_unix_epoch_time(datetime.datetime.strptime(sub.createdOn.split(".")[0], "%Y-%m-%dT%H:%M:%S"))
		if timeSubmit > roundStart and timeSubmit <= roundEnd:
			if status.get("annotations") is not None:
				if status.annotations.get("stringAnnos") is not None:
					team = filter(lambda x: x.get("key") == "team", status.annotations['stringAnnos'])
					if len(team) > 0:
						#print(sub)
						teamValue = team[0]['value']
						stat = status.status
						runStart = []
						runEnd = []
						if status.annotations.get("longAnnos") is not None:
							runStart = filter(lambda x: x.get("key") == "RUN_START", status.annotations['longAnnos'])
							runEnd = filter(lambda x: x.get("key") == "RUN_END", status.annotations['longAnnos'])
							if len(runStart) == 0 or len(runEnd) == 0:
								runStart = filter(lambda x: x.get("key") == "TRAINING_STARTED", status.annotations['longAnnos'])
								runEnd = filter(lambda x: x.get("key") == "TRAINING_LAST_UPDATED", status.annotations['longAnnos'])
						#Convert runtime to minutes
						runTime = math.ceil((runEnd[0]['value'] - runStart[0]['value'])/60000.0) if len(runStart) > 0 and len(runEnd) > 0 else float('nan')
						subDf = pd.DataFrame({"team":teamValue, "submissionId":status.id, "runTimeMinutes":runTime, "sc":subCh, "round":roundValue,"status":stat, "challenge":challenge}, index=[0])
						submissions = submissions.append(subDf)
	return(submissions)

#NCI PROTEOGENOMICS
statDf = pd.DataFrame()
CHALLENGE = "Proteogenomics"

ROUND_START = 0
ROUND_END = 1507705200000
ROUND_VALUE = 1
SUB_CH = 1
EVAL_ID = 8720143
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))
SUB_CH = 2
EVAL_ID = 8720145
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))
SUB_CH = 3
EVAL_ID = 8720149
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))

ROUND_START = 1507705200000
ROUND_END = 1509606000000
ROUND_VALUE = 2

SUB_CH = 1
EVAL_ID = 8720143
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))
SUB_CH = 2
EVAL_ID = 8720145
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))
SUB_CH = 3
EVAL_ID = 8720149
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))

ROUND_START = 1509606000000
ROUND_END = 15096060000001509606000000
ROUND_VALUE = "final"

SUB_CH = 1
EVAL_ID = 8720143
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))
SUB_CH = "2a"
EVAL_ID = 9608069
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))
SUB_CH = "2b"
EVAL_ID = 9608082
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))
SUB_CH = "3a"
EVAL_ID = 9608070
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))
SUB_CH = "3b"
EVAL_ID = 9608083
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))

#MM
CHALLENGE = "MM"

ROUND_START = 0
ROUND_END = 1505458800000
ROUND_VALUE = 1
SUB_CH = 1
EVAL_ID = 7997393
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))
SUB_CH = 2
EVAL_ID = 7997396
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))

ROUND_START = 1509001200000
ROUND_END = 1510214400000
SUB_CH = 3
EVAL_ID = 7997398
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))


ROUND_START = 1505458800000
ROUND_END = 1507705200000
ROUND_VALUE = 2
SUB_CH = 1
EVAL_ID = 7997393
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))
SUB_CH = 2
EVAL_ID = 7997396
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))

ROUND_START = 1510214400000
ROUND_END = 1510819200000
SUB_CH = 3
EVAL_ID = 7997398
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))


ROUND_START = 1507705200000
ROUND_END = 1509001200000
ROUND_VALUE = 3
SUB_CH = 1
EVAL_ID = 7997393
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))
SUB_CH = 2
EVAL_ID = 7997396
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))


ROUND_START = 1509001200000
ROUND_END = 15108192000001510819200000
ROUND_VALUE = "final"
SUB_CH = 1
EVAL_ID = 7997393
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))
SUB_CH = 2
EVAL_ID = 7997396
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))
SUB_CH = 3
EVAL_ID = 7997398
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))


#DM
CHALLENGE = "DM"

ROUND_VALUE = 1
ROUND_START = 0
ROUND_END = 1482541490864
SUB_CH = 1
EVAL_ID = 7453778
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))

ROUND_START = 0
ROUND_END = 1482565514894
SUB_CH = 2
EVAL_ID = 7453793
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))


ROUND_VALUE = 2
ROUND_START = 1482566436000
ROUND_END = 1486627236000
SUB_CH = 1
EVAL_ID = 7453778
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))

SUB_CH = 2
EVAL_ID = 7453793
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))


ROUND_VALUE = 3
ROUND_START = 1486756369000
ROUND_END = 1490298769000
SUB_CH = 1
EVAL_ID = 7453778
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))

SUB_CH = 2
EVAL_ID = 7453793
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))

ROUND_VALUE = "final"

ROUND_START = 1490639746000
ROUND_END = 14906397460001490639746000
SUB_CH = 1
EVAL_ID = 7453778
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))

SUB_CH = 2
EVAL_ID = 7453793
statDf = statDf.append(createDockerSubmissionStats(EVAL_ID, ROUND_START, ROUND_END, ROUND_VALUE, SUB_CH, CHALLENGE))

statDf.reset_index(inplace=True)

del statDf['index']

statDf.to_csv("dockerSubmission.csv",index=False,encoding='utf-8')

overallStats = pd.DataFrame()
for challenge in statDf['challenge'].unique():
	challengeDf = statDf[statDf['challenge'] == challenge]
	for sc in challengeDf['sc'].unique():
		scDf = challengeDf[challengeDf['sc'] == sc]
		for numRound in scDf["round"].unique():
			roundDf = scDf[scDf['round'] == numRound]
			scoredDf = roundDf[roundDf['status'] == "SCORED"]
			numUniqTeams = len(scoredDf['team'].unique())
			totalRunTime = scoredDf['runTimeMinutes'].sum()
			#This mean excludes NAs
			averageRunTime = scoredDf['runTimeMinutes'].mean()
			stats = pd.DataFrame({"teams":numUniqTeams, "round":numRound, "sc":sc, "status":"SCORED", "challenge":challenge,"averageRunTime":averageRunTime, "totalRunTime":totalRunTime, "numberSubmissions":len(scoredDf)}, index=[0])
			overallStats = overallStats.append(stats)

			invalidDf = roundDf[roundDf['status'] != "SCORED"]
			numUniqTeams = len(invalidDf['team'].unique())
			totalRunTime = invalidDf['runTimeMinutes'].sum()
			#This mean excludes NAs
			averageRunTime = invalidDf['runTimeMinutes'].mean()
			stats = pd.DataFrame({"teams":numUniqTeams, "round":numRound, "sc":sc, "status":"INVALID", "challenge":challenge,"averageRunTime":averageRunTime, "totalRunTime":totalRunTime, "numberSubmissions":len(invalidDf)}, index=[0])
			overallStats = overallStats.append(stats)

overallStats.to_csv("dockerStats.csv",index=False)