"""challengeutils command line client"""
import argparse
import json
import logging
import os

import pandas as pd
import synapseclient
from synapseclient.retry import _with_retry

from . import createchallenge
from . import mirrorwiki
from . import utils
from . import writeup_attacher
from . import permissions
from . import download_current_lead_submission as dl_cur
from . import helpers
from . import dockertools
from .__version__ import __version__

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def command_mirrorwiki(syn, args):
    """For all challenges, you should be editting the staging site and then
    using the merge script to mirror staging to live site.  The script will
    compare wiki titles between the staging and live site and update the live
    site with respect to what has changed on the staging site.  Note, this is
    different from copying the wikis. To copy the wikis, please look at
    synapseutils.

    >>> challengeutils mirrorwiki syn12345 syn23456
    """
    mirrorwiki.mirrorwiki(syn, args.entityid, args.destinationid,
                          args.forceupdate)


def command_createchallenge(syn, args):
    """Creates a challenge space in Synapse.  This pulls from a standard
    DREAM template and creates the Projects and Teams that you will need
    for a challenge.  For more information on all the components this function
    creates, please head to `challenge administration <https://docs.synapse.org/articles/challenge_administration.html>`_.

    >>> challengeutils createchallenge "Challenge Name Here"
    """
    createchallenge.main(syn, args.challengename, args.livesiteid)


def command_query(syn, args):
    """Command line convenience function to call evaluation queue query
    Evaluation queues offer a separate query service from the rest of Synapse.
    This query function will print the leaderboard in a csv format in standard
    out.  Proceed `here <https://docs.synapse.org/rest/GET/evaluation/submission/query.html>`_
    to learn more about this query service.

    >>> challengeutils query "select objectId, status from evaluation_12345"
    """
    querydf = pd.DataFrame(list(utils.evaluation_queue_query(
        syn, args.uri, args.limit, args.offset)))
    if args.render:
        # Check if submitterId column exists
        if querydf.get('submitterId') is not None:
            submitter_names = [utils._get_submitter_name(syn, submitterid)
                               for submitterid in querydf['submitterId']]
            querydf['submitterName'] = submitter_names
        # Check if createdOn column exists
        if querydf.get('createdOn') is not None:
            createdons = [synapseclient.utils.from_unix_epoch_time(createdon)
                          for createdon in querydf['createdOn']]
            querydf['createdOn'] = createdons
    if args.outputfile is not None:
        querydf.to_csv(args.outputfile, index=False)
    else:
        print(querydf.to_csv(index=False))


def command_change_status(syn, args):
    """Each submission has a status, this is a convenience function to change
    the status of a submission.  Here is a list of `valid statuses <https://rest-docs.synapse.org/rest/org/sagebionetworks/evaluation/model/SubmissionStatusEnum.html>`_

    >>> challengeutils changestatus 1234545 INVALID
    """
    print(utils.change_submission_status(syn, args.submissionid, args.status))


def command_writeup_attach(syn, args):
    """Most challenges require participants to submit a writeup.  Using the
    new archive-challenge-project-tool system of receiving writeups, this is
    a convenience function to merge the writeup and archived write up Synapse
    ids to the main challenge queue

    >>> challengeutils attachwriteup writeupid submissionqueueid
    """
    writeup_attacher.attach_writeup(syn, args.writeupqueue,
                                    args.submissionqueue)


def command_set_entity_acl(syn, args):
    """
    Sets permissions on entities for users or teams.  By default the user is
    public if there is no user or team specified and the default permission
    is view.

    >>> challengeutils setentityacl syn123545 user_or_team view
    """
    permissions.set_entity_permissions(syn, args.entityid,
                                       principalid=args.principalid,
                                       permission_level=args.permission_level)


def command_set_evaluation_acl(syn, args):
    """
    Sets permissions on queues for users or teams.  By default the user is
    public if there is no user or team specified and the default permission
    is view.

    >>> challengeutils setevaluationacl 12345 user_or_team score
    """
    permissions.set_evaluation_permissions(syn, args.evaluationid,
                                           principalid=args.principalid,
                                           permission_level=args.permission_level)  # noqa pylint: disable=line-too-long


def command_dl_cur_lead_sub(syn, args):
    dl_cur.download_current_lead_sub(
        syn,
        args.submissionid,
        args.status,
        args.cutoff_annotation,
        verbose=args.verbose)


def command_list_evaluations(syn, args):
    """Lists evaluation queues of a project

    >>> challengeutils listevaluations projectid
    """
    utils.list_evaluations(syn, args.projectid)


def command_download_submission(syn, args):
    submission_dict = utils.download_submission(syn, args.submissionid,
                                                download_location=args.download_location) # noqa pylint: disable=line-too-long
    if args.output:
        filepath = submission_dict['file_path']
        if filepath is not None:
            os.rename(filepath, 'submission-' + args.submissionid)
            filepath = 'submission-' + args.submissionid
        submission_dict['file_path'] = 'submission-' + args.submissionid
        with open(args.output, "w") as sub_out:
            json.dump(submission_dict, sub_out)
        logger.info(args.output)
    else:
        logger.info(submission_dict)


def command_annotate_submission_with_json(syn, args):
    _with_retry(lambda: utils.annotate_submission_with_json(syn, args.submissionid,  # noqa pylint: disable=line-too-long
                                                            args.annotation_values,  # noqa pylint: disable=line-too-long
                                                            to_public=args.to_public,  # noqa pylint: disable=line-too-long
                                                            force_change_annotation_acl=args.force_change_annotation_acl),  # noqa pylint: disable=line-too-long
                wait=3,
                retries=10,
                retry_status_codes=[412, 429, 500, 502, 503, 504],
                verbose=True)


def command_send_email(syn, args):
    """Command line interface to send Synapse email"""
    # Must escape the backslash and replace all \n with
    # html breaks
    message = args.message.replace("\\n", "<br>")
    syn.sendMessage(userIds=args.userids,
                    messageSubject=args.subject,
                    messageBody=message)


def command_kill_docker_over_quota(syn, args):
    """
    Sets an annotation on Synapse Docker submissions such that it will
    be terminated by the orchestrator. Usually applies to submissions
    that have been running for longer than the alloted time.

    >>> challengeutils killdockeroverquota evaluationid quota
    """
    helpers.kill_docker_submission_over_quota(syn, args.evaluationid,
                                              quota=args.quota)


def command_validate_docker(syn, args):
    """Validates Docker image"""
    invalid_reasons = ''
    try:
        valid = dockertools.validate_docker_submission(syn, args.submissionid)
    except ValueError as err:
        invalid_reasons = str(err)

    status = "VALIDATED" if valid else "INVALID"
    result = {'docker_image_errors': invalid_reasons,
              'docker_image_status': status}
    with open(args.results, 'w') as out:
        out.write(json.dumps(result))


def build_parser():
    """Builds the argument parser and returns the result."""
    parser = argparse.ArgumentParser(
        description='Challenge utility functions')

    parser.add_argument(
        "-c", "--synapse_config",
        default=synapseclient.client.CONFIG_FILE,
        help="credentials file")

    parser.add_argument('-v', '--version', action='version',
                        version='challengeutils {}'.format(__version__))

    subparsers = parser.add_subparsers(
        title='commands',
        description='The following commands are available:',
        help='For additional help: "challengeutils <COMMAND> -h"')

    parser_createchallenge = subparsers.add_parser(
        'createchallenge',
        help='Creates a challenge from a template')
    parser_createchallenge.add_argument(
        "challengename",
        help="Challenge name")
    parser_createchallenge.add_argument(
        "--livesiteid",
        help=("Option to specify the live site synapse Id"
              " there is already a live site"))
    parser_createchallenge.set_defaults(func=command_createchallenge)

    parser_mirrorwiki = subparsers.add_parser(
        'mirrorwiki',
        help=("This command mirrors wiki pages. It relies on the wiki titles "
              "between two Synapse Projects to be the same and will merge the "
              "updates from entity's wikis to destination's wikis. "
              "Do not confuse this function with copy wiki."))

    parser_mirrorwiki.add_argument(
        "entityid",
        type=str,
        help="Synapse Id of the project's wiki changes you have staged")
    parser_mirrorwiki.add_argument(
        "destinationid",
        type=str,
        help=('Synapse Id of project whose wiki you want to update'
              ' with the entityid'))
    parser_mirrorwiki.add_argument(
        "--forceupdate",
        action='store_true',
        help='Update the wikipages even if they are the same')
    parser_mirrorwiki.set_defaults(func=command_mirrorwiki)

    parser_query = subparsers.add_parser(
        'query',
        help='Queries on a evaluation queue')
    parser_query.add_argument(
        "uri",
        type=str,
        help="Synapse ID of the project's wiki you want to copy")
    parser_query.add_argument(
        "--outputfile",
        type=str,
        help="File that you want your query results to be written to."
             "If not specified, it is written as stdout.",
        default=None)
    parser_query.add_argument(
        "--render",
        action='store_true',
        help="Renders submitterId and createdOn values in leaderboard")
    parser_query.add_argument(
        "--limit",
        type=int,
        help='How many records should be returned per request',
        default=20)
    parser_query.add_argument(
        "--offset",
        type=int,
        default=0,
        help='At what record offset from the first should iteration start')
    parser_query.set_defaults(func=command_query)

    parser_change_status = subparsers.add_parser(
        'changestatus',
        help='Changes the status of a submission id')
    parser_change_status.add_argument(
        "submissionid",
        type=str,
        help="Synapse submission Id")
    parser_change_status.add_argument(
        "status",
        type=str,
        help='Status to change submission to')

    parser_change_status.set_defaults(func=command_change_status)

    parser_attach_writeup = subparsers.add_parser(
        'attachwriteup',
        help='Attach the write ups of a challenge to its main challenge queue')

    parser_attach_writeup.add_argument(
        "writeupqueue",
        type=str,
        help='Write up submission queue evaluation id')

    parser_attach_writeup.add_argument(
        "submissionqueue",
        type=str,
        help='Challenge submission queue evaluation id')
    parser_attach_writeup.set_defaults(func=command_writeup_attach)

    parser_set_entity_acl = subparsers.add_parser(
        'setentityacl',
        help='Sets the permissions of a Synapse Entity')
    parser_set_entity_acl.add_argument(
        "entityid",
        type=str,
        help='Entity Synapse id')
    parser_set_entity_acl.add_argument(
        "principalid",
        type=str,
        help='Synapse user or Team name/id')
    parser_set_entity_acl.add_argument(
        "permission_level",
        type=str,
        help='Permissions',
        choices=[
            'view', 'download', 'edit', 'edit_and_delete', 'admin', 'remove'])

    parser_set_entity_acl.set_defaults(func=command_set_entity_acl)

    parser_set_evaluation_acl = subparsers.add_parser(
        'setevaluationacl',
        help='Sets the permissions of a Synapse Evaluation Queue')

    parser_set_evaluation_acl.add_argument(
        "evaluationid",
        type=str,
        help='Synapse Evaluation Queue id')

    parser_set_evaluation_acl.add_argument(
        "principalid",
        type=str,
        help='Synapse user or Team name/id')

    parser_set_evaluation_acl.add_argument(
        "permission_level",
        type=str,
        help='Permissions',
        choices=['view', 'submit', 'score', 'admin', 'remove'])

    parser_set_evaluation_acl.set_defaults(func=command_set_evaluation_acl)

    parser_dl_cur_lead_sub = subparsers.add_parser(
        'download_current_lead_submission',
        help='Downloads current leading submission for participant')

    parser_dl_cur_lead_sub.add_argument(
        "-i", "--submissionid",
        required=True,
        help="Int, or str(int) for submissionid, of current submission.")

    parser_dl_cur_lead_sub.add_argument(
        "-s", "--status",
        required=True,
        help="Submission status")

    parser_dl_cur_lead_sub.add_argument(
        "-a", "--cutoff_annotation",
        default="met_cutoff")

    parser_dl_cur_lead_sub.add_argument(
        "-v", "--verbose",
        action='store_false')

    parser_dl_cur_lead_sub.set_defaults(func=command_dl_cur_lead_sub)

    parser_list_evals = subparsers.add_parser(
        'listevaluations',
        help='List all evaluation queues of a project')

    parser_list_evals.add_argument(
        "projectid",
        type=str,
        help='Synapse id of project')

    parser_list_evals.set_defaults(func=command_list_evaluations)

    parser_download_submission = subparsers.add_parser(
        'downloadsubmission',
        help='Download a Synapse submission')

    parser_download_submission.add_argument(
        "submissionid",
        type=str,
        help='Synapse id of submission')

    parser_download_submission.add_argument(
        "--download_location",
        type=str,
        help='Specify download location. Defaults to current working dir',
        default=".")

    parser_download_submission.add_argument(
        "--output",
        type=str,
        help='Output json results into a file')

    parser_download_submission.set_defaults(func=command_download_submission)

    parser_annotate_sub = subparsers.add_parser(
        'annotatesubmission',
        help='Annotate a Synapse submission with a json file')

    parser_annotate_sub.add_argument(
        "submissionid",
        help="Submission ID")
    parser_annotate_sub.add_argument(
        "annotation_values",
        help="JSON file of annotations with key:value pair")
    parser_annotate_sub.add_argument(
        "-p", "--to_public",
        help="Annotations are by default private except to queue "
             "administrator(s), so change them to be public",
        action='store_true')
    parser_annotate_sub.add_argument(
        "-f", "--force_change_annotation_acl",
        help="Ability to update annotations if the key has "
             "different ACLs, warning will occur if this parameter "
             "isn't specified and the same key has different ACLs",
        action='store_true')
    parser_annotate_sub.set_defaults(
        func=command_annotate_submission_with_json)

    parser_send_email = subparsers.add_parser(
        'sendemail',
        help='Send a Synapse email')

    parser_send_email.add_argument(
        "--userids",
        type=str,
        help='List of user ids',
        nargs="+",
        required=True)

    parser_send_email.add_argument(
        "--subject",
        type=str,
        help='Email message subject',
        required=True)

    parser_send_email.add_argument(
        "--message",
        type=str,
        help='Email message body',
        required=True)

    parser_send_email.set_defaults(func=command_send_email)


    parser_kill_docker = subparsers.add_parser(
        'killdockeroverquota',
        help='Kill Docker submissions over the quota')

    parser_kill_docker.add_argument(
        "evaluationid",
        type=str,
        help='Synapse evaluation queue id')

    parser_kill_docker.add_argument(
        "quota",
        type=int,
        help="Time quota submission has to run in milliseconds")
    parser_kill_docker.set_defaults(func=command_kill_docker_over_quota)

    parser_validate_docker = subparsers.add_parser(
        'validatedocker',
        help='Validate Docker container')

    parser_validate_docker.add_argument("-s", "--submissionid",
                                        required=True, help="Submission id")
    parser_validate_docker.add_argument("-r", "--results", required=True,
                                        help="validation results")
    parser_validate_docker.set_defaults(func=command_validate_docker)
    return parser


def synapse_login(synapse_config):
    try:
        syn = synapseclient.login(silent=True)
    except Exception:
        syn = synapseclient.Synapse(configPath=synapse_config)
        syn.login(silent=True)
    return(syn)


def main():
    args = build_parser().parse_args()
    syn = synapse_login(args.synapse_config)
    args.func(syn, args)


if __name__ == "__main__":
    main()
