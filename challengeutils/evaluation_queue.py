from synapseclient import Evaluation


def create_evaluation_queue(syn, name, description, parentId,
                            submissionInstructionsMessage):
    '''
    Convenience function to create Evaluation Queues

    Args:
        syn: Synpase object
        name: Name of evaluation queue
        description: Description of queue
        parentid: Synapse project id
        submissionInstructionsMessage: Instructions for submission

    Returns:
        Evalation Queue
    '''
    evaluation = Evaluation(
        name=name,
        description=description,
        contentSource=parentId,
        submissionInstructionsMessage=submissionInstructionsMessage)
    # submissionReceiptMessage="Thanks for submitting to %s!" % name)
    queue = syn.store(evaluation)
    return(queue)


def set_evaluation_quota(syn, evalid, quota=3):
    '''
    Sets evaluation submission limit quota
        {'firstRoundStart': u'2017-01-03T00:00:00.000Z',
        'numberOfRounds': 1,
        'roundDurationMillis': 3139200000,
        'submissionLimit': 6}

    Args:
        syn: Synapse object
        evalid: Evaluation id
        quota: Number of submissions
    '''
    quota1 = dict(submissionLimit=quota)
    e = syn.getEvaluation(evalid)
    e.quota = quota1
    e = syn.store(e)
