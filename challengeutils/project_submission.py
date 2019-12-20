"""
This module is responsible for attaching participant writeup submissions with
the main challenge queues.  It also archives(copies) projects since there isn't
currently an elegant way in Synapse to create snapshots of projects.
"""
from abc import ABCMeta, abstractmethod
import logging

import pandas as pd
from synapseclient.utils import id_of
from . import utils

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


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
    """
    Join queue 1 values with queue 2
    Filter joined queues to keep specific values
    Annotate queue 1 with respective queue 2 annotation values
    """
    def __init__(self, syn, queue1, queue2, joinby="submitterId",
                 status_key="status", annotation_keys=[]):
        self.syn = syn
        self.queue1 = queue1
        self.queue2 = queue2
        self.joinby = joinby
        self.status_key = status_key
        self.annotation_keys = annotation_keys

    def join(self):
        """Join leaderboards"""
        joineddf = join_evaluations(self.syn, self.queue1, self.queue2,
                                    self.joinby, how="inner")
        return joineddf

    @abstractmethod
    def filter(self, joineddf):
        """Filters joined queues"""

    def annotate(self, joineddf, annotation_keys):
        """Annotates queue1 with specified annotation keys"""
        joineddf.apply(lambda row:
                       utils.annotate_submission(self.syn,
                                                 row['objectId_x'],
                                                 row[annotation_keys].to_dict(),
                                                 annotation_keys),
                                                 axis=1)

    def __call__(self):
        """Joins, filters and annotates queue1"""
        joined_leaderboarddf = self.join()
        filtered_leaderboarddf = self.filter(joined_leaderboarddf)
        self.annotate(filtered_leaderboarddf,
                      annotation_keys=self.annotation_keys)


class JoinWriteupChallengeQueues(JoinFilterAnnotateQueues):
    """Join writeup queue with main challenge queue"""
    def filter(self, joineddf):
        """Filters joined queues"""
        # Filter joined leaderboard
        validated = joineddf[f'{self.status_key}_y'] == "VALIDATED"
        joineddf = joineddf[validated]
        scored = joineddf[f'{self.status_key}_x'] == "SCORED"
        joineddf = joineddf[scored]
        # Sort by submission id, because submission ids the bigger
        # the submission id, the more recent the submission
        joineddf = joineddf.sort_values("objectId_y", ascending=False)
        # Drop all duplicated so that one submission is linked with one
        # writeup. One writeup can be linked to many submissions, but not
        # the other way around
        joineddf.drop_duplicates('objectId_x', inplace=True)

        # Must rename writeup submission objectId or there will be conflict
        # entityId_y: writeUp Project ids
        # archived: archived Project ids
        column_remap = {'entityId_y': 'writeUp',
                        'archived': 'archivedWriteUp'}

        joineddf.rename(columns=column_remap, inplace=True)

        joineddf.drop_duplicates("submitterId", inplace=True)
        return joineddf
