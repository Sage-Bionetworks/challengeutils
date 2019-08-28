'''
This module is responsible for attaching participant writeup submissions with
the main challenge queues.  It also archives(copies) projects since there isn't
currently an elegant way in Synapse to create snapshots of projects.
'''
import logging
import time
import pandas as pd
import synapseclient
from synapseclient.annotations import to_submission_status_annotations
import synapseutils
from . import utils
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def archive_writeup(syn, submissionid, rearchive=False):
    '''
    Archive one writeup submission

    Args:
        syn: Synapse object
        submissionid: Synapse submission objectId
        rearchive: Boolean value to rearchive a project or not
    '''
    # retrieve file into cache and copy it to destination
    sub = syn.getSubmission(submissionid, downloadFile=False)
    sub_status = syn.getSubmissionStatus(submissionid)
    check_if_archived = filter(lambda x: x.get("key") == "archived",
                               sub_status.annotations['stringAnnos'])
    # check_if_archived will be an empty list if the annotation doesnt exist
    if not list(check_if_archived) or rearchive:
        submission_name = sub.entity.name
        current_time_ms = int(round(time.time() * 1000))
        archived_name = f"Archived {submission_name} {current_time_ms} {sub.id} {sub.entityId}"
        project_entity = synapseclient.Project(archived_name)
        entity = syn.store(project_entity)
        synapseutils.copy(syn, sub.entityId, entity.id)
        archived = {"archived": entity.id}
        sub_status = utils.update_single_submission_status(sub_status, archived)
        syn.store(sub_status)
        return entity.id
    return None


def archive_writeups(syn, evaluation, status="VALIDATED", rearchive=False):
    """
    Archive the submissions for the given evaluation queue and
    store them in the destination synapse folder.

    Args:
        evaluation: a synapse evaluation queue or its ID
        query: a query that will return the desired submissions.
               At least the ID must be returned. Defaults to:
               'select * from evaluation_[EVAL_ID] where status=="SCORED"'
    """
    if not isinstance(evaluation, synapseclient.Evaluation):
        evaluation = syn.getEvaluation(evaluation)

    logger.info(f"Archiving {evaluation.id} {evaluation.name}")
    logger.info("-" * 60)
    for sub, _ in syn.getSubmissionBundles(evaluation, status=status):
        archive_writeup(syn, sub.id, rearchive=rearchive)


def append_writeup_to_main_submission(row, syn):
    '''
    Helper function that appends the write up synapse id and archived
    write up synapse id on the main submission

    Args:
        row: Dictionary row['submitterId'], row['objectId'], row['archived'],
             row['entityId']
        syn: synapse object
    '''
    if pd.isnull(row['entityId']):
        logger.info(f"NO WRITEUP: {row['submitterId']}")
    else:
        logger.info(f"ADD WRITEUP: {row['submitterId']}")
        status = syn.getSubmissionStatus(row['objectId'])
        add_writeup_dict = {'writeUp': row['entityId']}
        # If archiver hasnt been run, there won't be an archive
        if not pd.isnull(row['archived']) and row['archived'] is not None:
            add_writeup_dict['archivedWriteUp'] = row['archived']
        else:
            archive_id = archive_writeup(syn, row['writeup_submissionid'])
            add_writeup_dict['archivedWriteUp'] = archive_id
        add_writeup = to_submission_status_annotations(add_writeup_dict,
                                                       is_private=False)
        new_status = utils.update_single_submission_status(status,
                                                           add_writeup)
        syn.store(new_status)


def attach_writeup(syn, writeup_queueid, submission_queueid):
    '''
    Attach the write up to the submission queue

    Args:
        writeup_queueid:   Write up evaluation queue id
        submission_queueid: Submission queue id
    '''
    writeup_query = (f"select objectId, submitterId, entityId, archived from evaluation_{writeup_queueid} "
                     "where status == 'VALIDATED'")
    writeups = list(utils.evaluation_queue_query(syn, writeup_query))
    submission_query = (f"select objectId, submitterId from evaluation_{submission_queueid} "
                        "where status == 'SCORED'")
    submissions = list(utils.evaluation_queue_query(syn, submission_query))
    writeupsdf = pd.DataFrame(writeups)
    submissionsdf = pd.DataFrame(submissions)
    # Must rename writeup submission objectId or there will be conflict
    writeupsdf.rename(columns={"objectId": "writeup_submissionid"}, inplace=True)
    submissions_with_writeupsdf = submissionsdf.merge(writeupsdf,
                                                      on="submitterId",
                                                      how="left")

    submissions_with_writeupsdf.apply(lambda row: append_writeup_to_main_submission(row, syn),
                                      axis=1)
