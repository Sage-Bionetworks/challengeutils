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


def _create_archive_writeup(syn, sub):
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
    project_entity = synapseclient.Project(archived_name)
    entity = syn.store(project_entity)
    synapseutils.copy(syn, sub.entityId, entity.id)
    return entity


def archive_writeup(syn, submissionid, rearchive=False):
    """
    Archive one writeup submission

    Args:
        syn: Synapse object
        submissionid: Synapse submission objectId
        rearchive: Boolean value to rearchive a project or not
    """
    # retrieve file into cache and copy it to destination
    sub = syn.getSubmission(submissionid, downloadFile=False)
    sub_status = syn.getSubmissionStatus(submissionid)
    # The .get accounts for if there is no stringAnnos
    check_if_archived = filter(lambda x: x.get("key") == "archived",
                               sub_status.annotations.get('stringAnnos', []))
    archived_entity = list(check_if_archived)
    # check_if_archived will be an empty list if the annotation doesnt exist
    if not archived_entity or rearchive:
        entity = _create_archive_writeup(syn, sub)
        archived = {"archived": entity.id}
        sub_status = utils.update_single_submission_status(sub_status,
                                                           archived)
        syn.store(sub_status)
        return entity.id
    return archived_entity[0]['value']


def archive_writeups(syn, evaluation, status="VALIDATED", rearchive=False):
    """
    Archive submissions for the given evaluation queue and
    store them in the destination synapse folder.

    Args:
        syn: Synapse object
        evaluation: a synapse evaluation queue or its ID
        status: Annotation status of a submission. Defaults to VALIDATED
        rearchive: Boolean value to rearchive a project or not

    Returns:
        List of archived entity ids
    """
    if not isinstance(evaluation, synapseclient.Evaluation):
        evaluation = syn.getEvaluation(evaluation)

    LOGGER.info(f"Archiving {evaluation.id} {evaluation.name}")
    LOGGER.info("-" * 60)
    archived = [archive_writeup(syn, sub.id, rearchive=rearchive)
                for sub, _ in syn.getSubmissionBundles(evaluation,
                                                       status=status)]
    return archived


def attach_writeup_to_main_submission(syn, row):
    """
    Attach the write up synapse id and archived write up synapse id on
    the main submission

    Args:
        syn: synapse object
        row: Dictionary row['submitterId'], row['objectId'], row['archived'],
             row['entityId'], row['writeup_submissionid'] (this is the
             submission id of the writeup)
    """
    if pd.isnull(row['entityId']):
        LOGGER.info(f"NO WRITEUP: {row['submitterId']}")
    else:
        LOGGER.info(f"ADD WRITEUP: {row['submitterId']}")
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


def archive_and_attach_writeups(syn, writeup_queueid, submission_queueid,
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
    writeup_query = ("select objectId, submitterId, entityId, archived "
                     f"from evaluation_{writeup_queueid} "
                     f"where {status_key} == 'VALIDATED'")
    writeups = list(utils.evaluation_queue_query(syn, writeup_query))
    submission_query = ("select objectId, submitterId from "
                        f"evaluation_{submission_queueid} "
                        f"where {status_key} == 'SCORED'")
    submissions = list(utils.evaluation_queue_query(syn, submission_query))

    writeupsdf = pd.DataFrame(writeups)
    submissionsdf = pd.DataFrame(submissions)
    # Must rename writeup submission objectId or there will be conflict
    writeupsdf.rename(columns={"objectId": "writeup_submissionid"},
                      inplace=True)
    submissions_with_writeupsdf = submissionsdf.merge(writeupsdf,
                                                      on="submitterId",
                                                      how="left")

    submissions_with_writeupsdf.apply(lambda row:
                                      attach_writeup_to_main_submission(syn,
                                                                        row),
                                      axis=1)
