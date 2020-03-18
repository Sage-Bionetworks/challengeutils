"""Run challenge invoker"""
#! /usr/bin/env python3
import argparse
import importlib
import logging
from datetime import timedelta

import synapseclient
from synapseclient.exceptions import SynapseAuthenticationError
from synapseclient.exceptions import SynapseNoCredentialsError

from scoring_harness import lock

logging.basicConfig(format='%(asctime)s %(message)s')
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


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


# ==================================================
#  Handlers for command
# ==================================================
def command(syn, evaluation_queue_maps, admin_user_ids=None, dry_run=False,
            remove_cache=False, send_messages=False, notifications=True):
    for queueid in evaluation_queue_maps:
        for config in evaluation_queue_maps[queueid]:
            invoke_func = config['func']
            invoke = invoke_func(syn, queueid,
                                 admin_user_ids=admin_user_ids,
                                 dry_run=dry_run,
                                 remove_cache=remove_cache,
                                 send_messages=send_messages,
                                 notifications=notifications,
                                 **config['kwargs'])
            invoke()


def main(args):
    """Main method that executes validate / scoring"""
    # Synapse login
    try:
        if args.synapse_config is not None:
            syn = synapseclient.Synapse(debug=args.debug,
                                        configPath=args.synapse_config)
        else:
            syn = synapseclient.Synapse(debug=args.debug)
        syn.login(silent=True)
    except (SynapseAuthenticationError, SynapseNoCredentialsError):
        raise ValueError("Must provide Synapse credentials as parameters or "
                         "through a Synapse config file.")

    # TODO: Check challenge admin ids
    if args.admin_user_ids is None:
        args.admin_user_ids = [syn.getUserProfile()['ownerId']]

    try:
        module = import_config_py(args.config_path)
    except Exception:
        raise ValueError("Error importing your python config script")

    check_keys = set(["id", "func", 'kwargs'])
    evaluation_queue_maps = {}
    for queue in module.EVALUATION_QUEUES_CONFIG:
        if not check_keys.issubset(queue.keys()):
            raise KeyError("You must specify 'id', 'func', 'kwargs'"
                           "for each of your evaluation queues"
                           "in your EVALUATION_QUEUES_CONFIG")
        # evaluation_queue_maps[queue['id']] = queue
        if evaluation_queue_maps.get(queue['id']):
            evaluation_queue_maps[queue['id']].append(queue)
        else:
            evaluation_queue_maps[queue['id']] = [queue]

    if args.evaluation:
        try:
            eval_queues = {evalid: evaluation_queue_maps[evalid]
                           for evalid in args.evaluation}
        except KeyError:
            raise ValueError("If evaluation is specified, must match an 'id' "
                             "in EVALUATION_QUEUES_CONFIG")
    else:
        eval_queues = evaluation_queue_maps

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
        command(syn, eval_queues, admin_user_ids=args.admin_user_ids,
                dry_run=args.dry_run, remove_cache=args.remove_cache,
                send_messages=args.send_messages,
                notifications=args.notifications)
    except Exception as e:
        LOGGER.error(e)

    update_lock.release()

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("config_path",
                        help="path to config.py")

    parser.add_argument("-c", "--synapse_config",
                        help="Path to Synapse Config File")

    parser.add_argument("--notifications",
                        help="Send error notifications to challenge admins",
                        action="store_true")

    parser.add_argument("--send-messages",
                        help="Send validation and scoring messages to participants",
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

    # Add these subparsers after because it takes multiple arguments
    parser.add_argument('-a',
                        "--admin-user-ids",
                        help="Synapse user ids. Defaults to the user running the script",
                        nargs='+',
                        default=None)

    parser.add_argument("--evaluation",
                        help="Evaluation id(s) to validate/score.  If not specified, script "
                             "will validate/score all evaluations set in EVALUATION_QUEUES_CONFIG",
                        nargs='+',
                        default=None)

    args = parser.parse_args()
    LOGGER.info("=" * 30)
    LOGGER.info("STARTING HARNESS")
    main(args)
    LOGGER.info("ENDING HARNESS")
    LOGGER.info("=" * 30)
