'''
Command line tool for validation and scoring Synapse challenges

To use this script, first install the Synapse Python Client
http://python-docs.synapse.org/

Author: thomas.yu
'''
import importlib
import logging
import os

from synapseclient import Evaluation

from synapseclient.annotations import to_submission_status_annotations
import challengeutils.utils
from . import messages

logging.basicConfig(format='%(asctime)s %(message)s')
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


def get_user_name(profile):
    '''
    Get name of Synapse user

    Args:
        profile: syn.getUserProfile()

    Returns:
        Synapse name or username
    '''
    names = []
    if 'firstName' in profile and profile['firstName']:
        names.append(profile['firstName'].strip())
    if 'lastName' in profile and profile['lastName']:
        names.append(profile['lastName'].strip())
    if not names:
        names.append(profile['userName'])
    return " ".join(names)


def import_config_py(config_path):
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


def _remove_cached_submission(submission_file):
    """Remove submission file if cache clearing is requested

    Args:
        submission_file: Input submission"""
    try:
        os.unlink(submission_file)
    except TypeError:
        pass

class Challenge:
    """Run Challenge Object"""
    def __init__(self, syn, dry_run=False, send_messages=False,
                 acknowledge_receipt=False, remove_cache=False):
        self.syn = syn
        self.dry_run = dry_run
        self.send_messages = send_messages
        self.acknowledge_receipt = acknowledge_receipt
        self.remove_cache = remove_cache

    def validate_single_submission(self, submission, status,
                                   validation_func, goldstandard_path):
        '''
        Validates a single submission

        Args:
            syn: Synapse object
            submission: Submission object
            status: Submission Status object
            validation_func: Function that validates (takes prediction filepath and
                             truth file)
            dry_run: Defaults to storing status (False)
            remove_cache: Removes submission file from cache (default: False)

        Return:
            is_valid - Boolean value for whether submission is valid
            validation_error - Type of Python error (Assertion, ValueError...)
            validation_message - Error message
        '''
        validation_error = None
        LOGGER.info("validating {} {}".format(submission.id, submission.name))
        try:
            # Account for if submissions aren't files
            if submission.filePath is None:
                submission_input = submission
            else:
                submission_input = submission.filePath
            is_valid, validation_message = validation_func(submission_input,
                                                           goldstandard_path)
        except Exception as ex1:
            is_valid = False
            LOGGER.error("Exception during validation: {} {} {}".format(type(ex1),
                                                                        ex1,
                                                                        str(ex1)))
            # ex1 only happens in this scope in python3,
            # so must store validation_error as a variable
            validation_error = ex1
            validation_message = str(ex1)

        status.status = "VALIDATED" if is_valid else "INVALID"

        if not is_valid:
            failure_reason = {"FAILURE_REASON": validation_message[0:1000]}
        else:
            failure_reason = {"FAILURE_REASON": ''}

        add_annotations = to_submission_status_annotations(failure_reason,
                                                           is_private=False)
        status = challengeutils.utils.update_single_submission_status(
            status, add_annotations)

        if not self.dry_run:
            status = self.syn.store(status)
        return (is_valid, validation_error, validation_message)

    def validate(self,
                 queue_info_dict,
                 admin_user_ids,
                 challenge_synid,
                 status='RECEIVED'):
        '''
        Validates all submissions with status = 'RECEIVED' by default and
        emails participants with validation results

        Args:
            syn: Synapse object
            queue_info_dict: dictionary with id, scoring_func,
                            and goldstandard_path as keys
            admin_user_ids: list of Synapse user profile ids of admin users
            challenge_synid: Synapse id of challenge project
            status: submissions with this status to validate. Default to
                    RECEIVED
            send_messages: Send messages
            acknowledge_receipt: Send validation results
            dry_run: Do not update Synapse
            remove_cache: Clear cache of submission files
        '''
        evaluation = queue_info_dict['id']
        validation_func = queue_info_dict['validation_func']
        goldstandard_path = queue_info_dict['goldstandard_path']

        if not isinstance(evaluation, Evaluation):
            evaluation = self.syn.getEvaluation(evaluation)

        LOGGER.info("Validating {} {}".format(evaluation.id, evaluation.name))
        LOGGER.info("-" * 20)

        submission_bundles = self.syn.getSubmissionBundles(evaluation, status=status)
        for submission, sub_status in submission_bundles:
            # refetch the submission so that we get the file path
            # to be later replaced by a "downloadFiles" flag on
            # getSubmissionBundles
            submission = self.syn.getSubmission(submission)

            is_valid, error, message = self.validate_single_submission(submission,
                                                                       sub_status,
                                                                       validation_func,
                                                                       goldstandard_path)

            # Remove submission file if cache clearing is requested.
            if self.remove_cache:
                _remove_cached_submission(submission.filePath)
            # send message AFTER storing status to ensure
            # we don't get repeat messages
            profile = self.syn.getUserProfile(submission.userId)
            if is_valid:
                messages.validation_passed(syn=self.syn,
                                           userids=[submission.userId],
                                           acknowledge_receipt=self.acknowledge_receipt,
                                           dry_run=self.dry_run,
                                           username=get_user_name(profile),
                                           queue_name=evaluation.name,
                                           submission_id=submission.id,
                                           submission_name=submission.name,
                                           challenge_synid=challenge_synid)
            else:
                if isinstance(error, AssertionError):
                    send_to = [submission.userId]
                    username = get_user_name(profile)
                else:
                    send_to = admin_user_ids
                    username = "Challenge Administrator"

                messages.validation_failed(syn=self.syn,
                                           userids=send_to,
                                           send_messages=self.send_messages,
                                           dry_run=self.dry_run,
                                           username=username,
                                           queue_name=evaluation.name,
                                           submission_id=submission.id,
                                           submission_name=submission.name,
                                           message=message,
                                           challenge_synid=challenge_synid)
        LOGGER.info("-" * 20)

    def score_single_submission(self, submission, status,
                                scoring_func, goldstandard_path):
        '''
        Scores a single submission

        Args:
            syn: Synapse object
            submission: Submission object
            status: Submission Status object
            scoring_func: Function that scores (takes prediction filepath and
                        truth file)
            dry_run: Defaults to storing status (False)
            remove_cache: Removes submission after scoring (default: False)

        Return:
            status - Annotated submission status
            message - scoring message (errors/success)
        '''
        status.status = "INVALID"
        try:
            sub_scores, message = scoring_func(
                submission.filePath, goldstandard_path)

            LOGGER.info(f"scored: {submission.id} {submission.name} "
                        f"{submission.userId} {sub_scores}")

            add_annotations = to_submission_status_annotations(sub_scores,
                                                               is_private=True)
            status = challengeutils.utils.update_single_submission_status(
                status, add_annotations)
            status.status = "SCORED"

        except Exception as ex1:
            LOGGER.error(
                f'Error scoring submission {submission.name} {submission.id}:')
            LOGGER.error(f'{type(ex1)} {ex1} {str(ex1)}')
            # ex1 only happens in this scope in python3,
            # so must store message as a variable
            message = str(ex1)

        if not self.dry_run:
            status = self.syn.store(status)
        return(status, message)


    def score(self,
              queue_info_dict,
              admin_user_ids,
              challenge_synid,
              status='VALIDATED'):
        '''
        Score all submissions with status = 'VALIDATED' by default and
        emails participants with scores

        Args:
            syn: Synapse object
            queue_info_dict: dictionary with id, scoring_func,
                            and goldstandard_path as keys
            admin_user_ids: list of Synapse user profile ids of admin users
            challenge_synid: Synapse id of challenge project
            status: submissions with this status to score. Default to
                    VALIDATED
            send_messages: Send messages
            send_notifications: Send notifications
            dry_run: Do not update Synapse
            remove_cache: Clear cache of scored submissions
        '''
        evaluation = queue_info_dict['id']
        scoring_func = queue_info_dict['scoring_func']
        goldstandard_path = queue_info_dict['goldstandard_path']

        if not isinstance(evaluation, Evaluation):
            evaluation = self.syn.getEvaluation(evaluation)

        LOGGER.info(f'Scoring {evaluation.id} {evaluation.name}')
        LOGGER.info("-" * 20)
        submission_bundle = self.syn.getSubmissionBundles(evaluation, status=status)
        for submission, sub_status in submission_bundle:
            # refetch the submission so that we get the file path
            submission = self.syn.getSubmission(submission)
            # If goldstandard path is None, skip scoring
            if goldstandard_path is None:
                continue
            status, message = self.score_single_submission(submission, sub_status,
                                                           scoring_func,
                                                           goldstandard_path)
            # Remove submission file after scoring if requested.
            if self.remove_cache:
                _remove_cached_submission(submission.filePath)
            # send message AFTER storing status to ensure
            # we don't get repeat messages
            profile = self.syn.getUserProfile(submission.userId)

            if status.status == 'SCORED':
                messages.scoring_succeeded(syn=self.syn,
                                           userids=[submission.userId],
                                           send_messages=self.send_messages,
                                           dry_run=self.dry_run,
                                           message=message,
                                           username=get_user_name(profile),
                                           queue_name=evaluation.name,
                                           submission_name=submission.name,
                                           submission_id=submission.id,
                                           challenge_synid=challenge_synid)
            else:
                messages.scoring_error(syn=self.syn,
                                       userids=admin_user_ids,
                                       send_messages=self.send_messages,
                                       dry_run=self.dry_run,
                                       message=message,
                                       username="Challenge Administrator,",
                                       queue_name=evaluation.name,
                                       submission_name=submission.name,
                                       submission_id=submission.id,
                                       challenge_synid=challenge_synid)
        LOGGER.info("-" * 20)
