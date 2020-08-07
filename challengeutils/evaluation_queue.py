"""Evaluation Queue helper functions"""
from abc import ABCMeta, abstractmethod
from concurrent.futures import ThreadPoolExecutor
import importlib
import json
import logging
import os
import time

import synapseclient
from synapseclient import Synapse
from synapseclient.core.exceptions import (SynapseHTTPError,
                                           SynapseAuthenticationError,
                                           SynapseNoCredentialsError)

from .annotations import update_submission_status
from .utils import update_single_submission_status

logging.basicConfig(format='%(asctime)s %(message)s')
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


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


def _remove_cached_submission(submission_file):
    """
    Remove submission file if cache clearing is requested

    Args:
        submission_file: Input submission

    """
    try:
        os.unlink(submission_file)
    except TypeError:
        pass


class SubmissionInfo:
    """Submission information to return after evaluation

    Attributes:
        valid: A boolean value, True if your submission is 'valid'
        error: A Python Exception (e.g ValueError)
        annotations: A dictionary containing whatever values you want to
                     annotate your submission with

    """
    def __init__(self, valid: bool, error: Exception = None,
                 annotations: dict = None):
        self.valid = valid
        self.error = error
        self.annotations = {} if annotations is None else annotations


class QueueEvaluator(metaclass=ABCMeta):
    """Evaluate all submissions of specific status in an evaluation queue

    Attributes:
        _status: retrieve all submissions of this status to evaluate
        _success_status: Set success status
    """
    # Status of submissions to evaluaate
    _status = "RECEIVED"
    # Successful submissions will be placed in this status
    _success_status = "ACCEPTED"

    def __init__(self, syn, evaluation, dry_run=False,
                 remove_cache=False, concurrent_submissions=1,
                 **kwargs):
        """Init EvaluationQueueProcessor

        Args:
            syn: Synapse object
            evaluation: synapseclient.Evaluation object
            dry_run: Do not update Synapse. Default is False.
            remove_cache: Removes submission file from cache.
                          Default is False.
            concurrent_submissions: Number of concurrent submissions
                                    to run.
            **kwargs: kwargs
        """
        self.syn = syn
        self.dry_run = dry_run
        self.evaluation = syn.getEvaluation(evaluation)
        self.remove_cache = remove_cache
        self.concurrent_submissions = concurrent_submissions
        self.kwargs = kwargs

    def evaluate(self):
        """Evalute all submissions of a specific status of a queue"""
        evaluation_str = (f"Evaluating Queue: {self.evaluation.name} "
                          f"({self.evaluation.id})")
        LOGGER.info("-" * len(evaluation_str))
        LOGGER.info(evaluation_str)
        submission_bundles = self.syn.getSubmissionBundles(self.evaluation,
                                                           status=self._status)
        # Use x number of threads to execute submissions in parallel
        with ThreadPoolExecutor(self.concurrent_submissions) as executor:
            for submission, sub_status in submission_bundles:
                executor.submit(self.evaluate_and_update, submission,
                                sub_status)
        LOGGER.info("-" * len(evaluation_str))

    @abstractmethod
    def _evaluation_function(self, submission, **kwargs) -> SubmissionInfo:
        """User determined evaluation function

        Args:
            submission: synapseclient.Submission object

        Returns:
            challengeutils.evaluation_queue.SubmissionInfo object

        """
        SubmissionInfo(valid=True, annotations={"key1": "annotations"})
        return SubmissionInfo

    def evaluate_and_update(self, submission, sub_status):
        """Evaluate submissions and stores submission annotations

        Args:
            submission: synapseclent.Submission object

        """
        if not self.dry_run:
            try:
                sub_status.status = "EVALUATION_IN_PROGRESS"
                sub_status = self.syn.store(sub_status)
            except SynapseHTTPError:
                # TODO: check code 412
                return
        LOGGER.info(f"Evaluation submission: {submission.id}")

        submission_info = self._evaluate_submission(submission)

        self._store_submission_annotations(sub_status, submission_info)

        # Remove submission file if cache clearing is requested.
        if self.remove_cache:
            _remove_cached_submission(submission.filePath)

    def _evaluate_submission(self, submission):
        """
        Evaluate submission function

        Args:
            submission: synapse Submission object

        Returns:
            challengeutils.evaluation_queue.SubmissionInfo object

        """
        # refetch the submission so that we get the file path
        # to be later replaced by a "downloadFiles" flag on
        # getSubmissionBundles
        submission = self.syn.getSubmission(submission)
        try:
            submission_info = self._evaluation_function(submission,
                                                        **self.kwargs)
        except Exception as ex1:
            LOGGER.error("Exception during validation: "
                         f"{type(ex1)} {ex1} {str(ex1)}")
            # TODO: allow for annotations to be added even if error
            # annotations = {}
            submission_info = SubmissionInfo(valid=False, error=ex1)
            # validation_message = str(ex1)
        return submission_info

    def _store_submission_annotations(self, sub_status, submission_info):
        """Store submission annotations

        Args:
            sub_status: Synapse Submission Status
            submission_info: challengeutils.evaluation_queue.SubmissionInfo
                             object

        """
        annotations = submission_info.annotations
        is_valid = submission_info.valid
        status = self._success_status if is_valid else "INVALID"

        sub_status = update_single_submission_status(sub_status,
                                                     annotations,
                                                     is_private=False)
        sub_status = update_submission_status(sub_status, annotations,
                                              status=status)
        if not self.dry_run:
            sub_status = self.syn.store(sub_status)
        else:
            LOGGER.debug(sub_status)


def _import_config_py(config_path):
    '''
    Uses importlib to import users configuration

    Args:
        config_path: Path to configuration python script

    Returns:
        module
    '''
    spec = importlib.util.spec_from_file_location("config", config_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evaluate_queue(syn, python_config, json_config,
                   **kwargs):
    """Main method that executes the evaluation of queues

    Args:
        syn: synapseclient connection
        python_config: This script will contain the python function you want
                       to apply on your submissions.
                       See 'templates/evaluate_submission.py' for an example.
        json_config: The json configuration links your python class with the
                     evaluation queue.
                     See 'templates/evaluation_config.json' for an example.
        **kwargs: arguments from QueueEvaluator
            dry_run: Do not update Synapse. Default is False.
            remove_cache: Removes submission file from cache.
                          Default is False.
            concurrent_submissions: Number of concurrent submissions
                                    to run.
    """

    with open(json_config, 'r') as json_f:
        config = json.load(json_f)

    for queue_name in config:
        queue_config = config[queue_name]
        try:
            module = _import_config_py(python_config)
            evaluator_cls = getattr(module, queue_config['evaluator'])
        except Exception:
            raise ValueError("Error importing your python config script")

        evaluator_cls(syn, queue_config['evaluation_queue_id'],
                      **kwargs).evaluate()
