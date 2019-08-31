'''
Command line tool for validation and scoring Synapse challenges

To use this script, first install the Synapse Python Client
http://python-docs.synapse.org/

Author: thomas.yu
'''
from datetime import timedelta
import importlib
import logging
import os

import synapseclient
from synapseclient import Evaluation
from synapseclient.exceptions import SynapseAuthenticationError
from synapseclient.exceptions import SynapseNoCredentialsError
from synapseclient.annotations import to_submission_status_annotations
import challengeutils.utils
from . import lock, messages

logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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


def validate_single_submission(syn, submission, status,
                               validation_func, goldstandard_path,
                               dry_run=False, remove_cache=False):
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
    logger.info("validating {} {}".format(submission.id, submission.name))
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
        logger.error("Exception during validation: {} {} {}".format(type(ex1),
                                                                    ex1,
                                                                    str(ex1)))
        # ex1 only happens in this scope in python3,
        # so must store validation_error as a variable
        validation_error = ex1
        validation_message = str(ex1)

    status.status = "VALIDATED" if is_valid else "INVALID"

    # Remove submission file if cache clearing is requested.
    if remove_cache:
        try:
            os.unlink(submission_input)
        except TypeError:
            pass

    if not is_valid:
        failure_reason = {"FAILURE_REASON": validation_message[0:1000]}
    else:
        failure_reason = {"FAILURE_REASON": ''}

    add_annotations = to_submission_status_annotations(failure_reason,
                                                       is_private=False)
    status = challengeutils.utils.update_single_submission_status(
        status, add_annotations)

    if not dry_run:
        status = syn.store(status)
    return (is_valid, validation_error, validation_message)


def validate(syn,
             queue_info_dict,
             admin_user_ids,
             challenge_synid,
             status='RECEIVED',
             send_messages=False,
             acknowledge_receipt=False,
             dry_run=False,
             remove_cache=False):
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
        evaluation = syn.getEvaluation(evaluation)

    logger.info("Validating {} {}".format(evaluation.id, evaluation.name))
    logger.info("-" * 20)

    submission_bundles = syn.getSubmissionBundles(evaluation, status=status)
    for submission, sub_status in submission_bundles:
        # refetch the submission so that we get the file path
        # to be later replaced by a "downloadFiles" flag on
        # getSubmissionBundles
        submission = syn.getSubmission(submission)

        is_valid, error, message = validate_single_submission(syn, submission, sub_status,
                                                              validation_func, goldstandard_path,
                                                              dry_run=dry_run,
                                                              remove_cache=remove_cache)
        # send message AFTER storing status to ensure
        # we don't get repeat messages
        profile = syn.getUserProfile(submission.userId)
        if is_valid:
            messages.validation_passed(syn=syn,
                                       userids=[submission.userId],
                                       acknowledge_receipt=acknowledge_receipt,
                                       dry_run=dry_run,
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

            messages.validation_failed(syn=syn,
                                       userids=send_to,
                                       send_messages=send_messages,
                                       dry_run=dry_run,
                                       username=username,
                                       queue_name=evaluation.name,
                                       submission_id=submission.id,
                                       submission_name=submission.name,
                                       message=message,
                                       challenge_synid=challenge_synid)
    logger.info("-" * 20)


def score_single_submission(syn, submission, status,
                            scoring_func, goldstandard_path,
                            dry_run=False, remove_cache=False):
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

        logger.info(
            f"scored: {submission.id} {submission.name} {submission.userId} {score}")

        add_annotations = to_submission_status_annotations(sub_scores,
                                                           is_private=True)
        status = challengeutils.utils.update_single_submission_status(
            status, add_annotations)
        status.status = "SCORED"

        # Remove submission file after scoring if requested.
        if remove_cache:
            os.unlink(submission.filePath)

    except Exception as ex1:
        logger.error(
            f'Error scoring submission {submission.name} {submission.id}:')
        logger.error(f'{type(ex1)} {ex1} {str(ex1)}')
        # ex1 only happens in this scope in python3,
        # so must store message as a variable
        message = str(ex1)

    if not dry_run:
        status = syn.store(status)
    return(status, message)


def score(syn,
          queue_info_dict,
          admin_user_ids,
          challenge_synid,
          status='VALIDATED',
          send_messages=False,
          send_notifications=False,
          dry_run=False,
          remove_cache=False):
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
        evaluation = syn.getEvaluation(evaluation)

    logger.info(f'Scoring {evaluation.id} {evaluation.name}')
    logger.info("-" * 20)
    submission_bundle = syn.getSubmissionBundles(evaluation, status=status)
    for submission, sub_status in submission_bundle:
        # refetch the submission so that we get the file path
        submission = syn.getSubmission(submission)
        # If goldstandard path is None, skip scoring
        if goldstandard_path is None:
            continue
        status, message = score_single_submission(syn, submission, sub_status,
                                                  scoring_func, goldstandard_path,
                                                  dry_run=dry_run, remove_cache=remove_cache)

        # send message AFTER storing status to ensure
        # we don't get repeat messages
        profile = syn.getUserProfile(submission.userId)

        if status.status == 'SCORED':
            messages.scoring_succeeded(syn=syn,
                                       userids=[submission.userId],
                                       send_messages=send_messages,
                                       dry_run=dry_run,
                                       message=message,
                                       username=get_user_name(profile),
                                       queue_name=evaluation.name,
                                       submission_name=submission.name,
                                       submission_id=submission.id,
                                       challenge_synid=challenge_synid)
        else:
            messages.scoring_error(syn=syn,
                                   userids=admin_user_ids,
                                   send_messages=send_messages,
                                   dry_run=dry_run,
                                   message=message,
                                   username="Challenge Administrator,",
                                   queue_name=evaluation.name,
                                   submission_name=submission.name,
                                   submission_id=submission.id,
                                   challenge_synid=challenge_synid)
    logger.info("-" * 20)


# ==================================================
#  Handlers for commands
# ==================================================
def command_validate(syn, evaluation_queue_maps, args):
    '''
    Validate command handler
    '''
    if args.evaluation is None:
        for queueid in evaluation_queue_maps:
            validate(syn,
                     evaluation_queue_maps[queueid],
                     args.admin_user_ids,
                     args.challenge_synid,
                     send_messages=args.send_messages,
                     acknowledge_receipt=args.acknowledge_receipt,
                     dry_run=args.dry_run,
                     remove_cache=args.remove_cache)
    else:
        validate(syn,
                 evaluation_queue_maps[args.evaluation],
                 args.admin_user_ids,
                 args.challenge_synid,
                 send_messages=args.send_messages,
                 acknowledge_receipt=args.acknowledge_receipt,
                 dry_run=args.dry_run,
                 remove_cache=args.remove_cache)


def command_score(syn, evaluation_queue_maps, args):
    '''
    Score command handler
    '''
    if args.evaluation is None:
        for queueid in evaluation_queue_maps:
            score(syn,
                  evaluation_queue_maps[queueid],
                  args.admin_user_ids,
                  args.challenge_synid,
                  send_messages=args.send_messages,
                  send_notifications=args.notifications,
                  dry_run=args.dry_run,
                  remove_cache=args.remove_cache)
    else:
        score(syn,
              evaluation_queue_maps[args.evaluation],
              args.admin_user_ids,
              args.challenge_synid,
              send_messages=args.send_messages,
              send_notifications=args.notifications,
              dry_run=args.dry_run,
              remove_cache=args.remove_cache)


def main(args):
    '''
    Main method that executes validate / scoring
    '''
    # Synapse login
    try:
        syn = synapseclient.Synapse(debug=args.debug)
        syn.login(email=args.user, password=args.password, silent=True)
    except (SynapseAuthenticationError, SynapseNoCredentialsError):
        raise ValueError(
            "Must provide Synapse credentials as parameters or "
            "store them as environmental variables.")

    # Check challenge synid
    try:
        challenge_ent = syn.get(args.challenge_synid)
        challenge_name = challenge_ent.name
    except Exception:
        raise ValueError(
            "Must provide correct Synapse id of challenge site or "
            "have permissions to access challenge the site")

    # TODO: Check challenge admin ids
    if args.admin_user_ids is None:
        args.admin_user_ids = [syn.getUserProfile()['ownerId']]

    try:
        module = import_config_py(args.config_path)
    except Exception:
        raise ValueError("Error importing your python config script")

    check_keys = set(
        ["id", "validation_func", "scoring_func", "goldstandard_path"])
    evaluation_queue_maps = {}
    for queue in module.EVALUATION_QUEUES_CONFIG:
        if not check_keys.issubset(queue.keys()):
            raise KeyError("You must specify 'id', 'validation_func', 'scoring_func', "
                           "'goldstandard_path' for each of your evaluation queues"
                           "in your EVALUATION_QUEUES_CONFIG")
        evaluation_queue_maps[queue['id']] = queue

    if args.evaluation is not None:
        check_queue_in_config = [eval_queue in evaluation_queue_maps
                                 for eval_queue in args.evaluation]
        if not all(check_queue_in_config):
            raise ValueError("If evaluation is specified, must match an 'id' "
                             "in EVALUATION_QUEUES_CONFIG")
    # Acquire lock, don't run two scoring scripts at once
    try:
        update_lock = lock.acquire_lock_or_fail('challenge',
                                                max_age=timedelta(hours=4))
    except lock.LockedException:
        logger.error("Is the scoring script already running? "
                     "Can't acquire lock.")
        # can't acquire lock, so return error code 75 which is a
        # temporary error according to /usr/include/sysexits.h
        return 75

    try:
        args.func(syn, evaluation_queue_maps, args)
    except Exception as ex1:
        logger.error('Error in challenge.py:')
        logger.error(f'{type(ex1)} {ex1} {str(ex1)}')
        if args.admin_user_ids:
            messages.error_notification(syn=syn,
                                        send_notifications=args.notifications,
                                        userids=args.admin_user_ids,
                                        dry_run=args.dry_run,
                                        message=str(ex1),
                                        queue_name=challenge_name)

    finally:
        update_lock.release()
    return 0
