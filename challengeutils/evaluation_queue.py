"""Evaluation Queue helper functions"""
import datetime
import time

import synapseclient


def _convert_date_to_epoch(date_string):
    """Converts local dates in YEAR-MM-DDTHH:MM:SS format
    (ie. 2020-02-21T23:53:27) to UTC epochtime in milliseconds and
    timestring"""
    local_time_struct = time.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
    epochtime = time.mktime(local_time_struct)
    utc_time_struct = time.gmtime(epochtime)
    return {"time_string": time.strftime("%Y-%m-%dT%H:%M:%S.000Z",
                                         utc_time_struct),
            "epochtime_ms": int(epochtime*1000)}


class SubmissionQuota:
    """A SubmissionQuota object
    https://rest-docs.synapse.org/rest/org/sagebionetworks/evaluation/model/SubmissionQuota.html
    """
    def __init__(self, round_start: str = None, round_end: str = None,
                 number_of_rounds: int = None, round_duration: str = None,
                 submission_limit: int = None):
        """
        Args:
            round_start: Start of round (local time) in YEAR-MM-DDTHH:MM:SS
                         format (ie. 2020-02-21T23:53:27)
            round_end: End of round (local time) in YEAR-MM-DDTHH:MM:SS format
                       (ie. 2020-02-21T23:53:27)
            number_of_rounds: Number of rounds
            round_duration: Round duration in milliseconds
            submission_limit: Number of submissions allowed per team

        """
        if round_end and round_duration:
            raise ValueError("Can only specify round_end or round_duration")
        if round_end and not round_start:
            raise ValueError("If specify round_end, but specify round_start")
        if round_start:
            round_start_info = _convert_date_to_epoch(round_start)
            round_start_utc = round_start_info['epochtime_ms']
            # Must set the time in UTC time, but must pass in local time
            # into function
            round_start = round_start_info['time_string']
        self.firstRoundStart = round_start
        if round_end:
            round_end_info = _convert_date_to_epoch(round_end)
            round_duration = round_end_info['epochtime_ms'] - round_start_utc
        self.roundDurationMillis = round_duration
        self.numberOfRounds = number_of_rounds
        self.submissionLimit = submission_limit


def set_evaluation_quota(syn, evalid: str, **kwargs):
    """Sets evaluation submission limit quota

    Args:
        syn: Synapse object
        evalid: Evaluation id
        **kwargs: same arguments as SubmissionQuota

    Returns:
        A synapseclient.Evaluation
    """
    quota = SubmissionQuota(**kwargs)
    evaluation = syn.getEvaluation(evalid)
    evaluation.quota = vars(quota)
    evaluation = syn.store(evaluation)
    return evaluation
