import argparse
import pandas as pd
import synapseclient
from . import createchallenge
from . import mirrorwiki
from . import utils
from . import writeup_attacher
from . import permissions
from . import download_current_lead_submission as dl_cur
from . import helpers


def command_mirrorwiki(syn, args):
    mirrorwiki.mirrorwiki(
        syn, args.entityid, args.destinationid, args.forceupdate)


def command_createchallenge(syn, args):
    createchallenge.createchallenge(syn, args.challengename, args.livesiteid)


def command_query(syn, args):
    querydf = pd.DataFrame(list(utils.evaluation_queue_query(
        syn, args.uri, args.limit, args.offset)))
    if args.outputfile is not None:
        querydf.to_csv(args.outputfile, index=False)
    else:
        print(querydf.to_csv(index=False))


def command_change_status(syn, args):
    print(utils.change_submission_status(syn, args.submissionid, args.status))


def command_writeup_attach(syn, args):
    writeup_attacher.attach_writeup(
        syn, args.writeupqueue, args.submissionqueue)


def command_set_entity_acl(syn, args):
    permissions.set_entity_permissions(
        syn, args.entityid,
        principalid=args.principalid,
        permission_level=args.permission_level)


def command_set_evaluation_acl(syn, args):
    permissions.set_evaluation_permissions(
        syn, args.evaluationid,
        principalid=args.principalid,
        permission_level=args.permission_level)


def command_dl_cur_lead_sub(syn, args):
    dl_cur.download_current_lead_sub(
        syn,
        args.submissionid,
        args.status,
        args.cutoff_annotation,
        verbose=args.verbose)


def command_make_hook_sub_invalid(syn, args):
    helpers.make_submission_status_invalid(syn, args.evaluationid)


def build_parser():
    """Builds the argument parser and returns the result."""
    parser = argparse.ArgumentParser(
        description='Challenge utility functions')
    '''
    parser.add_argument('-u', '--username', dest='synapseUser',
                         help='Username used to connect to Synapse')
    parser.add_argument('-p', '--password', dest='synapsePassword',
                         help='Password used to connect to Synapse')

    '''
    parser.add_argument(
        "-c", "--synapse_config",
        default=synapseclient.client.CONFIG_FILE,
        help="credentials file")

    subparsers = parser.add_subparsers(
        title='commands',
        description='The following commands are available:',
        help='For additional help: "challengeutils <COMMAND> -h"')

    parser_createChallenge = subparsers.add_parser(
        'createchallenge',
        help='Creates a challenge from a template')
    parser_createChallenge.add_argument(
        "challengename",
        help="Challenge name")
    parser_createChallenge.add_argument(
        "--livesiteid",
        help=("Option to specify the live site synapse Id"
              " there is already a live site"))
    parser_createChallenge.set_defaults(func=command_createchallenge)

    parser_mirrorWiki = subparsers.add_parser(
        'mirrorwiki',
        help=("This command mirrors wiki pages. It relies on the wiki titles "
              "between two Synapse Projects to be the same and will merge the "
              "updates from entity's wikis to destination's wikis. "
              "Do not confuse this function with copy wiki."))

    parser_mirrorWiki.add_argument(
        "entityid",
        type=str,
        help="Synapse Id of the project's wiki changes you have staged")
    parser_mirrorWiki.add_argument(
        "destinationid",
        type=str,
        help=('Synapse Id of project whose wiki you want to update'
              ' with the entityid'))
    parser_mirrorWiki.add_argument(
        "--forceupdate",
        action='store_true',
        help='Update the wikipages even if they are the same')
    parser_mirrorWiki.set_defaults(func=command_mirrorwiki)

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

    parser_make_sub_invalid = subparsers.add_parser('makehooksubinvalid',
                                                    help='Changes submission status with invalid prediction file to invalid')
    parser_make_sub_invalid.add_argument("evaluationid",
                                         type=str,
                                         help="Synapse evaluation id")

    parser_make_sub_invalid.set_defaults(func=command_make_hook_sub_invalid)

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

    return parser


def perform_main(syn, args):
    if 'func' in args:
        try:
            args.func(syn, args)
        except Exception:
            raise


def synapse_login(synapse_config):
    try:
        syn = synapseclient.login(silent=True)
    except Exception:
        syn = synapseclient.Synapse(configPath=synapse_config, silent=True)
        syn.login()
    return(syn)


def main():
    args = build_parser().parse_args()
    syn = synapse_login(args.synapse_config)
    perform_main(syn, args)


if __name__ == "__main__":
    main()
