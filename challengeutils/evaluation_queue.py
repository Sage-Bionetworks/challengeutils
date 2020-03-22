from abc import ABCMeta, abstractmethod
import logging

import pandas as pd
from synapseclient.utils import id_of
from synapseclient import Evaluation
from . import utils

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


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


def join_evaluations(syn, evaluation1, evaluation2, joinby, how="inner"):
    """
    Join two evaluation queues in a pandas dataframe

    Args:
        evaluation1: first `synapseclient.Evaluation` or its id
        evaluation2: second `synapseclient.Evaluation` or its id
        on: Column to join by
        how: Type of merge to be performed. Default to inner.

    Returns:
        Joined evaluations
    """
    evaluationid1 = id_of(evaluation1)
    evaluationid2 = id_of(evaluation2)

    eval1_query = f"select * from evaluation_{evaluationid1}"
    evaluation1_results = list(utils.evaluation_queue_query(syn, eval1_query))
    evaluation1df = pd.DataFrame(evaluation1_results)

    eval2_query = f"select * from evaluation_{evaluationid2}"
    evaluation2_results = list(utils.evaluation_queue_query(syn, eval2_query))
    evaluation2df = pd.DataFrame(evaluation2_results)
    joineddf = evaluation1df.merge(evaluation2df, on=joinby, how=how)
    return joineddf


class JoinFilterAnnotateQueues(metaclass=ABCMeta):
    """Joins queue 1 values with queue 2, then filters joined queues to
    keep specific values.  Annotates queue 1 with respective queue 2
    annotation values

    Args:
        syn: Synapse object
        queue1: Evaluation queue 1
        queue2: Evaluation queue 2
        keys: List of annotation keys from queue2 to annotate queue1
        **kwargs: joinby, how. See JoinFilterAnnotateQueues.join()

    """
    def __init__(self, syn, queue1, queue2, keys: list = None,
                 **kwargs):
        self.syn = syn
        self.queue1 = queue1
        self.queue2 = queue2
        self.keys = [] if keys is None else keys
        self.kwargs = kwargs

    def join(self, joinby="submitterId", how="inner"):
        """Join leaderboards

        Args:
            joinby: Join two queues by a column. Defaults to `submitterId`
            how: How to join the two queues. {'left', 'right', 'outer',
                 'inner'} Default 'inner'.
                * left: use calling frame's index (or column if on is
                        specified)
                * right: use `other`'s index.
                * outer: form union of calling frame's index (or column if on
                         is specified) with `other`'s index, and sort it.
                         lexicographically.
                * inner: form intersection of calling frame's index (or column
                         if on is specified) with `other`'s index, preserving
                         the order of the calling's one.

        Returns:
            Joined pandas.DataFrame()

        """
        joineddf = join_evaluations(self.syn, self.queue1, self.queue2,
                                    joinby, how=how)
        return joineddf

    @abstractmethod
    def filter(self, joineddf):
        """Filters joined queues"""

    def annotate(self, joineddf):
        """Annotates queue1 with specified annotation keys"""
        joineddf.apply(lambda row:
                       # It is always objectId_x because this is the
                       # submission id of the first queue
                       utils.annotate_submission(self.syn,
                                                 row['objectId_x'],
                                                 row[self.keys].to_dict(),
                                                 self.keys),
                       axis=1)

    def __call__(self):
        """Joins, filters and annotates queue1"""
        joined_leaderboarddf = self.join(**self.kwargs)
        filtered_leaderboarddf = self.filter(joined_leaderboarddf)
        self.annotate(filtered_leaderboarddf)
