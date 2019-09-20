"""
This module is responsible for attaching participant writeup submissions with
the main challenge queues.  It also archives(copies) projects since there isn't
currently an elegant way in Synapse to create snapshots of projects.
"""
import logging
import time
import pandas as pd
import synapseclient
from synapseclient.annotations import to_submission_status_annotations
import synapseutils
from . import utils
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


# def _create_copy_project(syn, entityid, project_name):
#     """
#     Create a copy of a project

#     Args:
#         syn: Synapse object
#         entityid: Synapse entity id
#         project_name: The new project name
#     """
#     project_entity = synapseclient.Project(new_project_name)
#     entity = syn.store(project_entity)
#     synapseutils.copy(syn, entityid, entity.id)
#     return entity


def _create_archive_project_submission(syn, sub):
    """
    Creates the archived writeup project

    Args:
        syn: Synapse object
        sub: Synapse submission

    Returns:
        Synapse Project entity
    """
    submission_name = sub.entity.name
    current_time_ms = int(round(time.time() * 1000))
    archived_name = (f"Archived {submission_name} {current_time_ms} "
                     f"{sub.id} {sub.entityId}")
    #entity = _create_copy_project(syn, sub.entityId, archived_name)
    project_entity = synapseclient.Project(archived_name)
    entity = syn.store(project_entity)
    synapseutils.copy(syn, sub.entityId, entity.id)
    return entity


def archive_project_submission(syn, submissionid, rearchive=False):
    """
    Archive one writeup submission by copying the submitted writeup
    Project into a new Project.

    Args:
        syn: Synapse object
        submissionid: Synapse submission objectId
        rearchive: Determine whether or not to re-archive the submitted
                   Project. Default to False.
    """
    # retrieve file into cache and copy it to destination
    sub = syn.getSubmission(submissionid, downloadFile=False)
    sub_status = syn.getSubmissionStatus(submissionid)
    # The .get accounts for if there is no stringAnnos
    archived_entity = [x for x in sub_status.annotations.get('stringAnnos', [])
                       if x.get("key") == "archived"]
    # archived_entity will be an empty list if the annotation doesnt exist
    if not archived_entity or rearchive:
        entity = _create_archive_project_submission(syn, sub)
        archived = {"archived": entity.id}
        sub_status = utils.update_single_submission_status(sub_status,
                                                           archived)
        syn.store(sub_status)
        return entity.id
    return archived_entity[0]['value']


def archive_project_submissions(syn, evaluation, status="VALIDATED",
                                rearchive=False):
    """
    Archive submissions for an evaluation queue that accepts writeup
    submissions as Projects and store them in the destination synapse
    folder.

    Args:
        syn: Synapse object
        evaluation: a synapse evaluation queue or its ID
        status: Annotation status of a submission. Defaults to VALIDATED
        rearchive: Determine whether or not to re-archive the submitted
                   Project. Default to False.
    Returns:
        List of archived entity ids
    """
    if not isinstance(evaluation, synapseclient.Evaluation):
        evaluation = syn.getEvaluation(evaluation)

    LOGGER.info(f"Archiving {evaluation.id} {evaluation.name}")
    LOGGER.info("-" * 60)
    archived = [archive_project_submission(syn, sub.id, rearchive=rearchive)
                for sub, _ in syn.getSubmissionBundles(evaluation,
                                                       status=status)]
    return archived

# This function already exists to an extent. annotate_submission_with_json
def add_annotations_to_submission(syn, submissionid, row, keys):
    """
    Attach the write up synapse id and archived write up synapse id on
    the main submission

    Args:
        syn: synapse object
        submissionid: submission id
        row: pd.Series or dict of submission annotations to add
        keys: list of keys to add to the submission
    """
    status = syn.getSubmissionStatus(submissionid)
    # Filter for only the keys to add to submission
    # Don't add if the value is null
    add_annotation_dict = {key: row[key] for key in keys
                           if pd.isnull(row[key])}
    # If archive hasnt been run, there won't be an archive
    add_annotations = to_submission_status_annotations(add_annotation_dict,
                                                       is_private=False)
    new_status = utils.update_single_submission_status(status,
                                                       add_annotations)
    syn.store(new_status)

# def _filter_joined_leaderboard(subs_and_writeupsdf):
#     validated = subs_and_writeupsdf[f'{status_key}_y'] == "VALIDATED"
#     subs_and_writeupsdf = subs_and_writeupsdf[validated]
#     scored = subs_and_writeupsdf[f'{status_key}_x'] == "SCORED"
#     subs_and_writeupsdf = subs_and_writeupsdf[scored]
#     return subs_and_writeupsdf

def join_queues(syn, queue1, queue2, joinby, how="inner"):
    """
    Join two evaluation queues in a pandas dataframe

    Args:
        queue1: Evaluation queue id 1
        queue2: Evaluation queue id 2
        joinby: Column to join by
        how: Type of merge to be performed. Default to inner.

    Returns:
        Joined queue
    """
    queue1_query = (f"select * from evaluation_{queue1}")
    queue1_results = list(utils.evaluation_queue_query(syn, queue1_query))
    queue1df = pd.DataFrame(queue1_results)

    queue2_query = (f"select * from evaluation_{queue2}")
    queue2_results = list(utils.evaluation_queue_query(syn, queue2_query))
    queue2df = pd.DataFrame(queue2_results)
    joineddf = queue1df.merge(queue2df, on=joinby, how=how)

    return joineddf


def archive_and_attach_project_submissions(syn, writeup_queueid,
                                           submission_queueid,
                                           status_key="STATUS"):
    """
    Attach the write up to the submission queue

    Args:
        syn: Synapse object
        writeup_queueid: Write up evaluation queue id
        submission_queueid: Submission queue id
        status_key: Submission status annotation key to look query.
                    Defaults to STATUS,
                    but could be prediction_file_status (workflowhook)
    """
    # archive_project_submissions(syn, writeup_queueid, status="VALIDATED",
    #                             rearchive=False)

    subs_and_writeupsdf = join_queues(syn, submission_queueid,
                                      writeup_queueid,
                                      joinby="submitterId",
                                      how="left")

    # if pd.isnull(row['entityId']):
    #     LOGGER.info(f"NO WRITEUP: {row['submitterId']}")
    # else:
    #     LOGGER.info(f"ADD WRITEUP: {row['submitterId']}")

    # Filter joined leaderboard
    # subs_and_writeupsdf = _filter_joined_leaderboard(subs_and_writeupsdf)
    validated = subs_and_writeupsdf[f'{status_key}_y'] == "VALIDATED"
    subs_and_writeupsdf = subs_and_writeupsdf[validated]
    scored = subs_and_writeupsdf[f'{status_key}_x'] == "SCORED"
    subs_and_writeupsdf = subs_and_writeupsdf[scored]
    # Sort by submission id, because submission ids the bigger the submission
    # id, the more recent the submission
    subs_and_writeupsdf = subs_and_writeupsdf.sort_values("objectId_y",
                                                          ascending=False)
    # Drop all duplicated so that one submission is linked with one writeup
    # One writeup can be linked to many submissions, but not the other way
    # around
    subs_and_writeupsdf.drop_duplicates('objectId_x', inplace=True)             
    
    # Must rename writeup submission objectId or there will be conflict
    # entityId_y: writeUp Project ids
    # archived: archived Project ids
    column_remap = {'entityId_y': 'writeUp',
                    'archived': 'archivedWriteUp'}

    subs_and_writeupsdf.rename(columns=column_remap,
                               inplace=True)

    subs_and_writeupsdf.drop_duplicates("submitterId", inplace=True)

    annotation_keys = ['writeUp', 'archivedWriteUp']

    for key in annotation_keys:
        # Add NA column if the column doesn't exist
        if subs_and_writeupsdf.get(key) is None:
            subs_and_writeupsdf[key] = float('nan')
        # Replace all None values with float('nan')
        else:
            null_ind = subs_and_writeupsdf[key].isnull()
            subs_and_writeupsdf[key][null_ind] = float('nan')

    # objectId_x: objectIds from submission queue
    subs_and_writeupsdf.apply(lambda row:
                              add_annotations_to_submission(syn,
                                                            row['objectId_x'],
                                                            row,
                                                            annotation_keys),
                              axis=1)
