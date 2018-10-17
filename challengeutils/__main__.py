import synapseclient
import argparse
import getpass
from challengeutils import createChallenge, mirrorWiki

def build_parser():
    """Builds the argument parser and returns the result."""
    parser = argparse.ArgumentParser(description='Challenge utility functions')
    # parser.add_argument('-u', '--username', dest='synapseUser',
    #                     help='Username used to connect to Synapse')
    # parser.add_argument('-p', '--password', dest='synapsePassword',
    #                     help='Password used to connect to Synapse')
    # parser.add_argument('-c', '--configPath', dest='configPath', default=synapseclient.client.CONFIG_FILE,
    #                     help='Path to configuration file used to connect to Synapse [default: %(default)s]')

    subparsers = parser.add_subparsers(title='commands',
                                       description='The following commands are available:',
                                       help='For additional help: "challengeutils <COMMAND> -h"')

    parser_createChallenge = subparsers.add_parser('createChallenge',
                                       help='Creates a challenge from a template')
    parser_createChallenge.add_argument("challengeName", help="Challenge name")
    parser_createChallenge.add_argument("--liveSite", help="Option to specify the live site synapse id when there is already a live site")
    parser_createChallenge.set_defaults(func=createChallenge.command_main)

    parser_mirrorWiki = subparsers.add_parser('mirrorWiki',
                                        help='Mirrors a staging site to live site.  Make sure that the wiki titles match.')
    parser_mirrorWiki.add_argument("id", type=str,
                        help="Synapse ID of the project's wiki you want to copy")
    parser_mirrorWiki.add_argument("destinationId", type=str,
                        help='Synapse ID of project where wiki will be copied to')
    parser_mirrorWiki.add_argument("--forceMerge", action='store_true',
                        help='Force the merge of wiki markdowns')
    parser_mirrorWiki.set_defaults(func=mirrorWiki.command_mergeWiki)
    
    return parser

def perform_main(syn, args):
    if 'func' in args:
        try:
            args.func(syn, args)
        except Exception as ex:
            raise

def synapseLogin():
    try:
        syn = synapseclient.login()
    except Exception as e:
        print("Please provide your synapse username/email and password (You will only be prompted once)")
        Username = raw_input("Username: ")
        Password = getpass.getpass()
        syn = synapseclient.login(email=Username, password=Password,rememberMe=True)
    return(syn)

def main():
    args = build_parser().parse_args()
    syn = synapseLogin()
    perform_main(syn, args)

if __name__ == "__main__":
    main()

