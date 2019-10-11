"""
This module is responsible for attaching participant writeup submissions with
the main challenge queues.  It also archives(copies) projects since there isn't
currently an elegant way in Synapse to create snapshots of projects.
"""
import logging
import time
import pandas as pd
import synapseclient
from synapseclient.utils import id_of
import synapseutils
from . import utils
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


def create_copy_project(syn, entityid, project_name):
    """
    Create a copy of a project, currently does not check if the project
    name specified already exists

    Args:
        syn: `synapseclient.Synapse` connection
        entityid: Synapse entity id
        project_name: The new project name
    """
    project_entity = synapseclient.Project(project_name)
    entity = syn.store(project_entity)
    synapseutils.copy(syn, entityid, entity.id)
    return entity


def _archive_project_submission(syn, submission):
    """
    Creates the archived writeup project

    Args:
        syn: `synapseclient.Synapse` connection
        submission: `synapseclient.Submission` object

    Returns:
        Archived `synapseclient.Project` object
    """
    submission_name = submission.entity.name
    current_time_ms = int(round(time.time() * 1000))
    archived_name = (f"Archived {submission_name} {current_time_ms} "
                     f"{submission.id} {submission.entityId}")
    archive_project_entity = create_copy_project(syn, submission.entityId,
                                                 archived_name)
    return archive_project_entity


def archive_project_submission(syn, submission, rearchive=False):
    """
    Archive one writeup submission by copying the submitted writeup
    Project into a new Project.

    Args:
        syn: `synapseclient.Synapse` connection
        submission: `synapseclient.Submission` or its id
        rearchive: Determine whether or not to re-archive the submitted
                   Project. Default to False.

    Returns:
        Synapse entity id of archived project
    """
    # retrieve file into cache and copy it to destination
    if not isinstance(submission, synapseclient.Submission):
        sub = syn.getSubmission(submission, downloadFile=False)
    sub_status = syn.getSubmissionStatus(submission)
    # The .get accounts for if there is no stringAnnos
    archived_entity = [x for x in sub_status.annotations.get('stringAnnos', [])
                       if x.get("key") == "archived"]
    # archived_entity will be an empty list if the annotation doesnt exist
    if not archived_entity or rearchive:
        LOGGER.info(f"Archiving project submission: {sub.id}")
        entity = _archive_project_submission(syn, sub)
        archived = {"archived": entity.id}
        sub_status = utils.update_single_submission_status(sub_status,
                                                           archived)
        syn.store(sub_status)
        return entity.id
    return archived_entity[0]['value']


def archive_project_submissions(syn, evaluation,
                                status_key="STATUS",
                                status="VALIDATED",
                                rearchive=False):
    """
    Archive submissions for an evaluation queue that accepts writeup
    submissions as Projects and store them in the destination synapse
    folder.

    Args:
        syn: `synapseclient.Synapse` connection
        evaluation: `synapseclient.Evaluation` or its id
        status: Annotation status of a submission. Defaults to VALIDATED
        rearchive: Determine whether or not to re-archive the submitted
                   Project. Default to False.

    Returns:
        List of archived entity ids
    """
    evaluationid = id_of(evaluation)
    LOGGER.info(f"Archiving queue: {evaluationid}")
    query = (f"select objectId from evaluation_{evaluationid} "
             f"where {status_key} == '{status}'")
    query_results = utils.evaluation_queue_query(syn, query)

    archived = [archive_project_submission(syn, query_result['objectId'],
                                           rearchive=rearchive)
                for query_result in query_results]
    return archived


def join_evaluations(syn, evaluation1, evaluation2, joinby, how="inner"):
    """
    Join two evaluation queues in a pandas dataframe

    Args:
        evaluation1: first `synapseclient.Evaluation` or its id
        evaluation2: second `synapseclient.Evaluation` or its id
        on: Column to join by
        how: Type of merge to be performed. Default to inner.

    Returns:
        Joined evaluations
    """
    evaluationid1 = id_of(evaluation1)
    evaluationid2 = id_of(evaluation2)

    eval1_query = f"select * from evaluation_{evaluationid1}"
    evaluation1_results = list(utils.evaluation_queue_query(syn, eval1_query))
    evaluation1df = pd.DataFrame(evaluation1_results)

    eval2_query = f"select * from evaluation_{evaluationid2}"
    evaluation2_results = list(utils.evaluation_queue_query(syn, eval2_query))
    evaluation2df = pd.DataFrame(evaluation2_results)
    joineddf = evaluation1df.merge(evaluation2df, on=joinby, how=how)
    return joineddf


# def _filter_joined_leaderboard(subs_and_writeupsdf):
#     validated = subs_and_writeupsdf[f'{status_key}_y'] == "VALIDATED"
#     subs_and_writeupsdf = subs_and_writeupsdf[validated]
#     scored = subs_and_writeupsdf[f'{status_key}_x'] == "SCORED"
#     subs_and_writeupsdf = subs_and_writeupsdf[scored]
#     return subs_and_writeupsdf


def archive_and_attach_project_submissions(syn, writeup_queueid,
                                           submission_queueid,
                                           status_key="STATUS"):
    """
    Attach the write up to the submission queue

    Args:
        syn: `synapseclient.Synapse` connection
        writeup_queueid: Write up evaluation queue id
        submission_queueid: Submission queue id
        status_key: Submission status annotation key to look query.
                    Defaults to STATUS,
                    but could be prediction_file_status (workflowhook)
    """
    archive_project_submissions(syn, writeup_queueid,
                                status_key=status_key,
                                status="VALIDATED",
                                rearchive=False)

    subs_and_writeupsdf = join_evaluations(syn, submission_queueid,
                                           writeup_queueid,
                                           joinby="submitterId",
                                           how="left")

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

    # None value is added because annotate_submission replies on an `is None`
    # check
    for key in annotation_keys:
        # Add column with None values if the column doesn't exist
        if subs_and_writeupsdf.get(key) is None:
            subs_and_writeupsdf[key] = None
        # Replace all float('nan') values with None
        else:
            null_ind = subs_and_writeupsdf[key].isnull()
            subs_and_writeupsdf[key][null_ind] = None

    # objectId_x: objectIds from submission queue
    subs_and_writeupsdf.apply(lambda row:
                              utils.annotate_submission(syn,
                                                        row['objectId_x'],
                                                        row[annotation_keys].to_dict(),
                                                        annotation_keys),
                              axis=1)
