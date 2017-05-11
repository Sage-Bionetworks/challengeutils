#
# Command line tool for scoring and managing Synapse challenges
#
# To use this script, first install the Synapse Python Client
# http://python-docs.synapse.org/
#
# Log in once using your user name and password
#   import synapseclient
#   syn = synapseclient.Synapse()
#   syn.login(<username>, <password>, rememberMe=True)
#
# Your credentials will be saved after which you may run this script with no credentials.
# 
# Author: chris.bare, thomasyu888
#
###############################################################################

import synapseclient
import synapseclient.utils as utils
from synapseclient.exceptions import *
from synapseclient import Activity
from synapseclient import Project, Folder, File
from synapseclient import Evaluation, Submission, SubmissionStatus
from synapseclient import Wiki
from synapseclient import Column
from synapseclient.dict_object import DictObject
from synapseclient.annotations import from_submission_status_annotations
import synapseutils as synu

from collections import OrderedDict
from datetime import datetime, timedelta
from itertools import izip
from StringIO import StringIO
import copy

import argparse
import json
import math
import os
import random
import re
import sys
import tarfile
import tempfile
import time
import traceback
import urllib
import uuid
import warnings
#Python scripts that are part of the challenge
import lock
try:
    import challenge_config as conf
except Exception as ex1:
    sys.stderr.write("\nPlease configure your challenge. See challenge_config.template.py for an example.\n\n")
    raise ex1

import messages


# the batch size can be bigger, we do this just to demonstrate batching
BATCH_SIZE = 20

# how many times to we retry batch uploads of submission annotations
BATCH_UPLOAD_RETRY_COUNT = 5

UUID_REGEX = re.compile('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')

# A module level variable to hold the Synapse connection
syn = None

def get_user_name(profile):
    names = []
    if 'firstName' in profile and profile['firstName'] and profile['firstName'].strip():
        names.append(profile['firstName'])
    if 'lastName' in profile and profile['lastName'] and profile['lastName'].strip():
        names.append(profile['lastName'])
    if len(names)==0:
        names.append(profile['userName'])
    return " ".join(names)

def update_single_submission_status(status, add_annotations, force=False):
    """
    This will update a single submission's status
    :param:    Submission status: syn.getSubmissionStatus()

    :param:    Annotations that you want to add in dict or submission status annotations format.
               If dict, all submissions will be added as private submissions
    """
    existingAnnotations = status.get("annotations", dict())

    privateAnnotations = {each['key']:each['value'] for annots in existingAnnotations for each in existingAnnotations[annots] if annots not in ['scopeId','objectId'] and each['isPrivate'] == True}
    publicAnnotations = {each['key']:each['value'] for annots in existingAnnotations for each in existingAnnotations[annots] if annots not in ['scopeId','objectId'] and each['isPrivate'] == False}

    if not synapseclient.annotations.is_submission_status_annotations(add_annotations):
        privateAddedAnnotations = add_annotations
        publicAddedAnnotations = dict()
    else:
        privateAddedAnnotations = {each['key']:each['value'] for annots in add_annotations for each in add_annotations[annots] if annots not in ['scopeId','objectId'] and each['isPrivate'] == True}
        publicAddedAnnotations = {each['key']:each['value'] for annots in add_annotations for each in add_annotations[annots] if annots not in ['scopeId','objectId'] and each['isPrivate'] == False} 
    #If you add a private annotation that appears in the public annotation, it switches 
    if sum([key in publicAddedAnnotations for key in privateAnnotations]) == 0:
        pass
    elif sum([key in publicAddedAnnotations for key in privateAnnotations]) >0 and force:
        privateAnnotations = {key:privateAnnotations[key] for key in privateAnnotations if key not in publicAddedAnnotations}
    else:
        raise ValueError("You are trying to add public annotations that are already part of the existing private annotations: %s.  Either change the annotation key or specify force=True" % ", ".join([key for key in privateAnnotations if key in publicAddedAnnotations]))
    if sum([key in privateAddedAnnotations for key in publicAnnotations]) == 0:
        pass
    elif sum([key in privateAddedAnnotations for key in publicAnnotations])>0 and force:
        publicAnnotations= {key:publicAnnotations[key] for key in publicAnnotations if key not in privateAddedAnnotations}
    else:
        raise ValueError("You are trying to add private annotations that are already part of the existing public annotations: %s.  Either change the annotation key or specify force=True" % ", ".join([key for key in publicAnnotations if key in privateAddedAnnotations]))

    privateAnnotations.update(privateAddedAnnotations)
    publicAnnotations.update(publicAddedAnnotations)

    priv = synapseclient.annotations.to_submission_status_annotations(privateAnnotations, is_private=True)
    pub = synapseclient.annotations.to_submission_status_annotations(publicAnnotations, is_private=False)

    for annotType in ['stringAnnos', 'longAnnos', 'doubleAnnos']:
        if priv.get(annotType) is not None and pub.get(annotType) is not None:
            if pub.get(annotType) is not None:
                priv[annotType].extend(pub[annotType])
            else:
                priv[annotType] = pub[annotType]
        elif priv.get(annotType) is None and pub.get(annotType) is not None:
            priv[annotType] = pub[annotType]

    status.annotations = priv
    return(status)

class Query(object):
    """
    An object that helps with paging through annotation query results.

    Also exposes properties totalNumberOfResults, headers and rows.
    """
    def __init__(self, query, limit=20, offset=0):
        self.query = query
        self.limit = limit
        self.offset = offset
        self.fetch_batch_of_results()

    def fetch_batch_of_results(self):
        uri = "/evaluation/submission/query?query=" + urllib.quote_plus("%s limit %s offset %s" % (self.query, self.limit, self.offset))
        results = syn.restGET(uri)
        self.totalNumberOfResults = results['totalNumberOfResults']
        self.headers = results['headers']
        self.rows = results['rows']
        self.i = 0

    def __iter__(self):
        return self

    def next(self):
        if self.i >= len(self.rows):
            if self.offset >= self.totalNumberOfResults:
                raise StopIteration()
            self.fetch_batch_of_results()
        values = self.rows[self.i]['values']
        self.i += 1
        self.offset += 1
        return values

def validate(evaluation, public=False, admin=None, dry_run=False):

    if type(evaluation) != Evaluation:
        evaluation = syn.getEvaluation(evaluation)

    print "\n\nValidating", evaluation.id, evaluation.name
    print "-" * 60
    sys.stdout.flush()
    if admin is not None:
        admin = syn.getUserProfile(admin)['userName']
    for submission, status in syn.getSubmissionBundles(evaluation, status='RECEIVED'):
        ex1 = None #Must define ex1 in case there is no error
        print "validating", submission.id, submission.name
        try:
            is_valid, validation_message = conf.validate_submission(evaluation, submission, public, admin)
        except Exception as ex1:
            is_valid = False
            print "Exception during validation:", type(ex1), ex1, ex1.message
            traceback.print_exc()
            validation_message = str(ex1)
        addannotations = {}
        #Add team name
        if 'teamId' in submission:
            team = syn.restGET('/team/{id}'.format(id=submission.teamId))
            if 'name' in team:
                addannotations['team'] = team['name']
            else:
                addannotations['team'] = submission.teamId
        elif 'userId' in submission:
            profile = syn.getUserProfile(submission.userId)
            addannotations['team'] = get_user_name(profile)
        else:
            addannotations['team'] = '?'
        status.status = "VALIDATED" if is_valid else "INVALID"
        if not is_valid:
            addannotations["FAILURE_REASON"] = validation_message
        else:
            addannotations["FAILURE_REASON"] = ''
        add_annotations = synapseclient.annotations.to_submission_status_annotations(addannotations,is_private=True)
        status = update_single_submission_status(status, add_annotations)

        if not dry_run:
            status = syn.store(status)
        ## send message AFTER storing status to ensure we don't get repeat messages
        profile = syn.getUserProfile(submission.userId)
        if is_valid:
            messages.validation_passed(
                userIds=[submission.userId],
                username=get_user_name(profile),
                queue_name=evaluation.name,
                submission_id=submission.id,
                submission_name=submission.name)
        else:
            if isinstance(ex1, AssertionError):
                sendTo = [submission.userId]
                username = get_user_name(profile)
            else:
                sendTo = conf.ADMIN_USER_IDS
                username = "Challenge Administrator"

            messages.validation_failed(
                userIds= sendTo,
                username=username,
                queue_name=evaluation.name,
                submission_id=submission.id,
                submission_name=submission.name,
                message=validation_message)

def archive(evaluation, stat="VALIDATED", reArchive=False):
    """
    Archive the submissions for the given evaluation queue and store them in the destination synapse folder.

    :param evaluation: a synapse evaluation queue or its ID
    :param query: a query that will return the desired submissions. At least the ID must be returned.
                  defaults to _select * from evaluation_[EVAL_ID] where status=="SCORED"_.
    """
    if type(evaluation) != Evaluation:
        evaluation = syn.getEvaluation(evaluation)

    print "\n\nArchiving", evaluation.id, evaluation.name
    print "-" * 60
    sys.stdout.flush()

    for submission, status in syn.getSubmissionBundles(evaluation, status=stat):
        ## retrieve file into cache and copy it to destination
        checkIfArchived = filter(lambda x: x.get("key") == "archived", status.annotations['stringAnnos'])
        if len(checkIfArchived)==0 or reArchive:
            projectEntity = Project('Archived %s %d %s %s' % (submission.name,int(round(time.time() * 1000)),submission.id,submission.entityId))
            entity = syn.store(projectEntity)
            adminPriv = ['DELETE','CREATE','READ','CHANGE_PERMISSIONS','UPDATE','MODERATE','CHANGE_SETTINGS']
            syn.setPermissions(entity,"3324230",adminPriv)
            copied = synu.copy(syn, submission.entityId, entity.id)
            archived = {"archived":entity.id}
            status = update_single_submission_status(status, archived)
            syn.store(status)

## ==================================================
##  Handlers for commands
## ==================================================
def command_check_status(args):
    submission = syn.getSubmission(args.submission)
    status = syn.getSubmissionStatus(args.submission)
    evaluation = syn.getEvaluation(submission.evaluationId)
    ## deleting the entity key is a hack to work around a bug which prevents
    ## us from printing a submission
    del submission['entity']
    print unicode(evaluation).encode('utf-8')
    print unicode(submission).encode('utf-8')
    print unicode(status).encode('utf-8')

def command_validate(args):
    # try:
    for evaluation in args.evaluation:
        validate(evaluation, args.public, dry_run=args.dry_run)
    # except:
    #     sys.stderr.write("\nValidate command requires either an evaluation ID or --all to validate all queues in the challenge")

def command_archive(args):
    archive(args.evaluation, args.status, args.reArchive)

## ==================================================
##  main method
## ==================================================

def main():

    global syn

    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--user", help="UserName", default=None)
    parser.add_argument("-p", "--password", help="Password", default=None)
    parser.add_argument("--challengeName", help="Challenge Name", required=True)
    parser.add_argument("--notifications", help="Send error notifications to challenge admins", action="store_true", default=False)
    parser.add_argument("--send-messages", help="Send validation and scoring messages to participants", action="store_true", default=False)
    parser.add_argument("--acknowledge-receipt", help="Send confirmation message on passing validation to participants", action="store_true", default=False)
    parser.add_argument("--dry-run", help="Perform the requested command without updating anything in Synapse", action="store_true", default=False)
    parser.add_argument("--debug", help="Show verbose error output from Synapse API calls", action="store_true", default=False)

    subparsers = parser.add_subparsers(title="subcommand")

    parser_status = subparsers.add_parser('status', help="Check the status of a submission")
    parser_status.add_argument("submission")
    parser_status.set_defaults(func=command_check_status)

    parser_validate = subparsers.add_parser('validate', help="Validate all RECEIVED submissions to an evaluation")
    parser_validate.add_argument("evaluation", metavar="EVALUATION-IDs", nargs='*', default=None)
    parser_validate.add_argument("--admin", metavar="ADMIN", default=False)
    parser_validate.add_argument("--public", action="store_true", default=False)
    parser_validate.set_defaults(func=command_validate)

    parser_archive = subparsers.add_parser('archive', help="Archive submissions to a challenge")
    parser_archive.add_argument("evaluation", metavar="EVALUATION-ID", default=None)
    parser_archive.add_argument("--status",metavar="STATUS", default="VALIDATED")
    parser_archive.add_argument("--reArchive", action="store_true", default=False)
    parser_archive.set_defaults(func=command_archive)

    args = parser.parse_args()

    print "\n" * 2, "=" * 75
    print datetime.utcnow().isoformat()

    ## Acquire lock, don't run two scoring scripts at once
    try:
        update_lock = lock.acquire_lock_or_fail('challenge', max_age=timedelta(hours=4))
    except lock.LockedException:
        print u"Is the scoring script already running? Can't acquire lock."
        # can't acquire lock, so return error code 75 which is a
        # temporary error according to /usr/include/sysexits.h
        return 75

    try:
        syn = synapseclient.Synapse(debug=args.debug)
        if not args.user:
            args.user = os.environ.get('SYNAPSE_USER', None)
        if not args.password:
            args.password = os.environ.get('SYNAPSE_PASSWORD', None)
        syn.login(email=args.user, password=args.password)

        ## initialize messages
        messages.syn = syn
        messages.dry_run = args.dry_run
        messages.send_messages = args.send_messages
        messages.send_notifications = args.notifications
        messages.acknowledge_receipt = args.acknowledge_receipt

        args.func(args)

    except Exception as ex1:
        sys.stderr.write('Error in scoring script:\n')
        st = StringIO()
        traceback.print_exc(file=st)
        sys.stderr.write(st.getvalue())
        sys.stderr.write('\n')

        if conf.ADMIN_USER_IDS:
            messages.error_notification(userIds=conf.ADMIN_USER_IDS, message=st.getvalue(), queue_name=args.challengeName)

    finally:
        update_lock.release()

    print "\ndone: ", datetime.utcnow().isoformat()
    print "=" * 75, "\n" * 2


if __name__ == '__main__':
    main()

