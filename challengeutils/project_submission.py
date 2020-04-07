"""
This module extends from JoinWriteupChallengeQueues and attaches
participant project submissions with the main challenge queues.
"""

from .evaluation_queue import JoinFilterAnnotateQueues

class JoinWriteupChallengeQueues(JoinFilterAnnotateQueues):
    """Join writeup queue with main challenge queue"""
    _status_key = "status"

    def filter(self, joineddf):
        """Filters joined queues"""
        # Filter joined leaderboard
        validated_idx = joineddf[f'{self._status_key}_y'] == "VALIDATED"
        joineddf = joineddf[validated_idx]
        scored_idx = joineddf[f'{self._status_key}_x'] == "SCORED"
        joineddf = joineddf[scored_idx]

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
