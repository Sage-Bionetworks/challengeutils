"""Run challenge invoker"""
#! /usr/bin/env python3
import argparse
import logging
from datetime import timedelta

import synapseclient
from synapseclient.exceptions import SynapseAuthenticationError
from synapseclient.exceptions import SynapseNoCredentialsError

import scoring_harness.challenge
from scoring_harness.challenge import validate, score, import_config_py
from scoring_harness.challenge import lock, messages


logging.basicConfig(format='%(asctime)s %(message)s')
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


# ==================================================
#  Handlers for commands
# ==================================================
def command_validate(syn, evaluation_queue_maps, args):
    """Validate command handler"""
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
    """Score command handler"""
    if args.evaluation is None:
        for queueid in evaluation_queue_maps:
            score(syn,
                  evaluation_queue_maps[queueid],
                  args.admin_user_ids,
                  args.challenge_synid,
                  send_messages=args.send_messages,
                  dry_run=args.dry_run,
                  remove_cache=args.remove_cache)
    else:
        score(syn,
              evaluation_queue_maps[args.evaluation],
              args.admin_user_ids,
              args.challenge_synid,
              send_messages=args.send_messages,
              dry_run=args.dry_run,
              remove_cache=args.remove_cache)


def main(args):
    """Main method that executes validate / scoring"""
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
        LOGGER.error("Is the scoring script already running? "
                     "Can't acquire lock.")
        # can't acquire lock, so return error code 75 which is a
        # temporary error according to /usr/include/sysexits.h
        return 75

    try:
        args.func(syn, evaluation_queue_maps, args)
    except Exception as ex1:
        LOGGER.error('Error in challenge.py:')
        LOGGER.error(f'{type(ex1)} {ex1} {str(ex1)}')
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("challenge_synid",
                        help="Synapse id of challenge project")
    parser.add_argument("config_path",
                        help="path to config.py")
    parser.add_argument("--evaluation",
                        help="Evaluation id(s) to validate/score.  If not specified, script "
                             "will validate/score all evaluations set in EVALUATION_QUEUES_CONFIG",
                        nargs='?',
                        default=None)

    parser.add_argument('-a',
                        "--admin-user-ids",
                        help="Synapse user ids. Defaults to the user running the script",
                        nargs='?',
                        default=None)

    parser.add_argument("-u",
                        "--user",
                        help="UserName",
                        default=None)

    parser.add_argument("-p",
                        "--password",
                        help="Password",
                        default=None)

    parser.add_argument("--notifications",
                        help="Send error notifications to challenge admins",
                        action="store_true")

    parser.add_argument("--send-messages",
                        help="Send validation and scoring messages to participants",
                        action="store_true")

    parser.add_argument("--acknowledge-receipt",
                        help="Send confirmation message on passing validation to participants",
                        action="store_true")

    parser.add_argument("--dry-run",
                        help="Perform the requested command without updating anything in Synapse",
                        action="store_true")

    parser.add_argument("--remove-cache",
                        help="If 'validate' step, removes invalid submissions from cache. "
                        "If 'score' step, removes scored submissions from cache.",
                        action="store_true")

    parser.add_argument("--debug",
                        help="Show verbose error output from Synapse API calls",
                        action="store_true")

    subparsers = parser.add_subparsers(title="subcommand")

    parser_validate = subparsers.add_parser('validate',
                                            help="Validate all RECEIVED submissions to an evaluation")
    parser_validate.set_defaults(
        func=scoring_harness.challenge.command_validate)

    parser_score = subparsers.add_parser('score',
                                         help="Score all VALIDATED submissions to an evaluation")
    parser_score.set_defaults(func=scoring_harness.challenge.command_score)

    args = parser.parse_args()
    LOGGER.info("=" * 30)
    LOGGER.info("STARTING HARNESS")
    main(args)
    LOGGER.info("ENDING HARNESS")
    LOGGER.info("=" * 30)
