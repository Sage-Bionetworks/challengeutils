import synapseclient
from synapseclient import Table
import pandas as pd
import datetime
import argparse

def updateDatabase(syn, database, new_dataset, databaseSynId, uniqueKeyCols, toDelete=False):
	"""
	Updates synapse tables by a row identifier with another dataset that has the same number and order of columns
	
	:param database:   	   The synapse table (pandas dataframe)
	:param new_dataset:    New dataset (pandas dataframe)
	:param databaseSynId   Synapse Id of the database table
	:param uniqueKeyCols:  Column(s) that make up the unique key

	:returns:      		   Don't know yet	
	"""
	checkBy = 'UNIQUE_KEY'
	database = database.fillna("")
	new_dataset = new_dataset.fillna("")
	#Columns must be in the same order
	new_dataset = new_dataset[database.columns]
	database[uniqueKeyCols] = database[uniqueKeyCols].applymap(str)
	database[checkBy] = database[uniqueKeyCols].apply(lambda x: ' '.join(x), axis=1)
	new_dataset[uniqueKeyCols] = new_dataset[uniqueKeyCols].applymap(str)
	new_dataset[checkBy] = new_dataset[uniqueKeyCols].apply(lambda x: ' '.join(x), axis=1)
	updateSet = new_dataset[new_dataset[checkBy].isin(database[checkBy])]
	updatingDatabase = database[database[checkBy].isin(new_dataset[checkBy])]

	allRowIds = database.index.values
	rowIds = updatingDatabase.index.values
	#If you input the exact same dataframe theres nothing to update
	if updateSet.empty and updatingDatabase.empty:
		differentRows = []
	else:
		allRowIds = database.index.values
		rowIds = updatingDatabase.index.values

		updateSet.index = updateSet[checkBy]
		updatingDatabase.index = updatingDatabase[checkBy]
		updateSet = updateSet.ix[updatingDatabase.index]
		differences = updateSet != updatingDatabase
		differentRows = differences.apply(sum, axis=1) >0 

	if sum(differentRows) > 0:
		updatingDatabase.ix[differentRows] = updateSet.ix[differentRows]
		toUpdate = updatingDatabase.ix[differentRows]
		toUpdate.index = [rowId for rowId, row in zip(rowIds, differentRows) if row]
		del toUpdate[checkBy]
		print("Updating rows")
		table = syn.store(Table(syn.get(databaseSynId), toUpdate))	
	else:
		print("No updated rows")
	#All deleted rows (This assumes that all data that don't show up in the new uploaded data should be deleted...)
	if toDelete:
		database.index = allRowIds
		deleteSets = database[~database[checkBy].isin(new_dataset[checkBy])]
		del deleteSets[checkBy]
		if not deleteSets.empty:
			print("Deleting Rows")
			deleteRows = syn.delete(Table(syn.get(databaseSynId), deleteSets))
		else:
			print("No deleted rows")
	#All new rows
	newSet =  new_dataset[~new_dataset[checkBy].isin(database[checkBy])]
	if not newSet.empty:
		print("Adding Rows")
		del newSet[checkBy]
		table = syn.store(Table(syn.get(databaseSynId), newSet))	
	else:
		print("No new rows")


def checkExists(annotValue):
	if len(annotValue)>0:
		return(annotValue[0]['value'])
	else:
		return(None)

def getSubmissionCount(syn, evalId, status="VALIDATED"):
	allSubs = pd.DataFrame()
	submissions = syn.getSubmissionBundles(evalId, status=status)
	for sub, stat in submissions:
		team = filter(lambda x: x.get("key") == "team", stat.annotations['stringAnnos'])
		submissionName = filter(lambda x: x.get("key") == "submissionName", stat.annotations['stringAnnos'])
		patientId = filter(lambda x: x.get("key") == "patientId", stat.annotations['stringAnnos'])
		roundNum = filter(lambda x: x.get("key") == "round", stat.annotations['stringAnnos'])
		team = checkExists(team)
		submissionName = checkExists(submissionName)
		patientId = checkExists(patientId)
		roundNum = checkExists(roundNum)
		timeSubmit = synapseclient.utils.to_unix_epoch_time(datetime.datetime.strptime(sub.createdOn.split(".")[0], "%Y-%m-%dT%H:%M:%S"))
		subDf = pd.DataFrame({"team":team, "submissionId":stat.id, "fileName":submissionName, "patientId":patientId, "round":roundNum, "dateTime":timeSubmit}, index=[0])
		allSubs = allSubs.append(subDf)
	return(allSubs)

def command_getSubmissionStats(syn, args):
	submission_stat_df = getSubmissionCount(syn, args.evalId, status=args.status)
	if args.databaseSynId is not None:
		database = syn.tableQuery('select * from %s'% args.databaseSynId)
		updateDatabase(syn, database.asDataFrame(), submission_stat_df, args.databaseSynId, ["submissionId"])
		print("Updated database")
	return(submission_stat_df)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Merge wiki')
	parser.add_argument("evalId", type=int,
						help="Evaluation Id of the Challenge Queue you want to get stats for")
	parser.add_argument("--databaseSynId", type=str,
						help='Database Table storing these challenge stats')
	parser.add_argument("--status", type=str, default="VALIDATED",
						help='Database Table storing these challenge stats')
	args = parser.parse_args()
	syn = synapseclient.login()
	command_getSubmissionStats(syn, args)
	


#evalId = 8116290
#status = "VALIDATED"
#submission_stat_df = getSubmissionCount(evalId, status)


