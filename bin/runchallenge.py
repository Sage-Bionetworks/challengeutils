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
#  Handlers for commands
# ==================================================
def command_validate(syn, evaluation_queue_maps):
    """Validate"""
    for queueid in evaluation_queue_maps:
        validator = evaluation_queue_maps[queueid]['validation_func']
        goldstandard = evaluation_queue_maps[queueid]['goldstandard_path']
        invoke = validator(syn, queueid, goldstandard_path=goldstandard)
        invoke()


def command_score(syn, evaluation_queue_maps):
    """Score"""
    for queueid in evaluation_queue_maps:
        scorer = evaluation_queue_maps[queueid]['scoring_func']
        goldstandard = evaluation_queue_maps[queueid]['goldstandard_path']
        invoke = scorer(syn, queueid, goldstandard_path=goldstandard)
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

    check_keys = set(["id", "validation_func", "scoring_func",
                      "goldstandard_path"])
    evaluation_queue_maps = {}
    for queue in module.EVALUATION_QUEUES_CONFIG:
        if not check_keys.issubset(queue.keys()):
            raise KeyError("You must specify 'id', 'validation_func', 'scoring_func', "
                           "'goldstandard_path' for each of your evaluation queues"
                           "in your EVALUATION_QUEUES_CONFIG")
        evaluation_queue_maps[queue['id']] = queue

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

    if args.validate:
        command_validate(syn, eval_queues)

    if args.score:
        command_score(syn, eval_queues)

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

    interact = parser.add_mutually_exclusive_group(required=True)

    interact.add_argument('--validate', action="store_true",
                          help="Validate RECEIVED submissions to an evaluation")
    interact.add_argument('--score', action="store_true",
                          help="Score VALIDATED submissions to an evaluation")

    args = parser.parse_args()
    LOGGER.info("=" * 30)
    LOGGER.info("STARTING HARNESS")
    main(args)
    LOGGER.info("ENDING HARNESS")
    LOGGER.info("=" * 30)
