#! /usr/bin/env python3
import argparse
import scoring_harness.challenge
import logging

logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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

    parser.add_argument("--debug",
                        help="Show verbose error output from Synapse API calls",
                        action="store_true")

    subparsers = parser.add_subparsers(title="subcommand")

    parser_validate = subparsers.add_parser('validate',
                                            help="Validate all RECEIVED submissions to an evaluation")
    parser_validate.set_defaults(func=scoring_harness.challenge.command_validate)

    parser_score = subparsers.add_parser('score',
                                         help="Score all VALIDATED submissions to an evaluation")
    parser_score.set_defaults(func=scoring_harness.challenge.command_score)

    args = parser.parse_args()
    logger.info("=" * 30)
    logger.info("STARTING HARNESS")
    scoring_harness.challenge.main(args)
    logger.info("ENDING HARNESS")
    logger.info("=" * 30)
