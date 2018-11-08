def createEvaluationQueue(syn, name, description, status, parentId, submissionInstructionsMessage):
	queue = syn.store(Evaluation(
	  name=name,
	  description=description,
	  status=status,
	  contentSource=parentId,
	  submissionInstructionsMessage=submissionInstructionsMessage,
	  submissionReceiptMessage="Thanks for submitting to %s!" % name))
	return(queue)


# {u'firstRoundStart': u'2017-01-03T00:00:00.000Z',
#   u'numberOfRounds': 1,
#   u'roundDurationMillis': 3139200000,
#   u'submissionLimit': 6}
def setQuota(syn,evalID,quota=3):
	quota1 = dict(submissionLimit = quota)
	e = syn.getEvaluation(evalID)
	e.quota = quota1
	e = syn.store(e)