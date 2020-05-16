"""Evaluation Queue helper functions"""
import time

from synapseclient import Synapse


def _convert_date_to_epoch(date_string):
    """Converts local time dates in YEAR-MM-DDTHH:MM:SS format
    (ie. 2020-02-21T23:53:27) to UTC epochtime in milliseconds and
    timestring

    Args:
        date_string: Local time date in YEAR-MM-DDTHH:MM:SS format
                     (ie. 2020-02-21T23:53:27)

    Returns:
        dict: {"time_string": UTC time in YEAR-MM-DDTHH:MM:SS format
               "epochtime_ms": UTC epoch time}

    """
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
    def __init__(self, firstRoundStart: str = None,
                 roundDurationMillis: int = None, numberOfRounds: int = None,
                 submissionLimit: int = None):
        self.firstRoundStart = firstRoundStart
        self.roundDurationMillis = roundDurationMillis
        self.numberOfRounds = numberOfRounds
        self.submissionLimit = submissionLimit


def _create_quota(round_start: str = None, round_end: str = None,
                  number_of_rounds: int = None, round_duration: int = None,
                  submission_limit: int = None) -> SubmissionQuota:
    """Creates the SubmissionQuota object

    Args:
        round_start: Start of round (local time) in YEAR-MM-DDTHH:MM:SS
                     format (ie. 2020-02-21T17:00:00)
        round_end: End of round (local time) in YEAR-MM-DDTHH:MM:SS format
                   (ie. 2020-02-21T19:00:00)
        number_of_rounds: Number of rounds
        round_duration: Round duration in milliseconds
        submission_limit: Number of submissions allowed per team

    Returns:
        SubmissionQuota object

    """
    if round_end is not None and round_duration is not None:
        raise ValueError("Can only specify round_end or round_duration")
    if round_end is not None and round_start is None:
        raise ValueError("If round_end is specified, "
                         "round_start must also be specified")

    if round_start:
        round_start_info = _convert_date_to_epoch(round_start)
        round_start_utc = round_start_info['epochtime_ms']
        # Must set the time in UTC time, but must pass in local time
        # into function
        round_start = round_start_info['time_string']

    if round_end:
        round_end_info = _convert_date_to_epoch(round_end)
        round_duration = round_end_info['epochtime_ms'] - round_start_utc

    if round_duration is not None and round_duration < 0:
        raise ValueError("Specified round_duration must be >= 0, or "
                         "round_end must be > round_start")

    quota = SubmissionQuota(firstRoundStart=round_start,
                            numberOfRounds=number_of_rounds,
                            roundDurationMillis=round_duration,
                            submissionLimit=submission_limit)
    return quota


def set_evaluation_quota(syn: Synapse, evalid: int, **kwargs):
    """Sets evaluation submission limit quota.  This WILL erase any old quota
    you had previously set. Note - round_start must be specified with either
    round_end or round_duration and number_of_rounds must be defined for the
    time limits to work.  submission_limit will work without number_of_rounds.

    Args:
        syn: Synapse object
        evalid: Evaluation id
        **kwargs:
            round_start: Start of round (local time) in YEAR-MM-DDTHH:MM:SS
                         format (ie. 2020-02-21T17:00:00)
            round_end: End of round (local time) in YEAR-MM-DDTHH:MM:SS format
                       (ie. 2020-02-21T19:00:00)
            number_of_rounds: Number of rounds
            round_duration: Round duration in milliseconds
            submission_limit: Number of submissions allowed per team

    Returns:
        A synapseclient.Evaluation

    Examples:
        >>> set_evaluation_quota(syn, 12345,
                                 round_start="2020-02-21T17:00:00",
                                 round_end="2020-02-23T17:00:00",
                                 number_of_rounds=1,
                                 submission_limit=3)

    """
    quota = _create_quota(**kwargs)
    evaluation = syn.getEvaluation(evalid)
    evaluation.quota = vars(quota)
    evaluation = syn.store(evaluation)
    return evaluation
