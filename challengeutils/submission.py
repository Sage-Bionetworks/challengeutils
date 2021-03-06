"""Functions that interact with submissions"""
import os
import re
import sys
import time
from typing import Union

import pandas as pd
import synapseutils
from synapseclient import (AUTHENTICATED_USERS, entity, Project, Synapse,
                           SubmissionViewSchema)
from synapseclient.annotations import to_submission_status_annotations
from synapseclient.core.exceptions import SynapseHTTPError
from synapseclient.core.utils import id_of

from . import dockertools
from . import permissions
from . import utils
from . import annotations

WORKFLOW_LAST_UPDATED_KEY = "orgSagebionetworksSynapseWorkflowOrchestratorWorkflowLastUpdated"
WORKFLOW_START_KEY = "orgSagebionetworksSynapseWorkflowOrchestratorExecutionStarted"
TIME_REMAINING_KEY = "orgSagebionetworksSynapseWorkflowOrchestratorTimeRemaining"


def append_writeup_to_main_submission(row, syn):
    '''
    Helper function that appends the write up synapse id and archived
    write up synapse id on the main submission

    Args:
        row: Dictionary row['team'], row['objectId'], row['archived'],
             row['entityId']
        syn: synapse object
    '''
    if pd.isnull(row['archived']):
        print("NO WRITEUP: " + row['submitterId'])
    else:
        status = syn.getSubmissionStatus(row['objectId'])
        add_writeup_dict = {
            'writeUp': row['entityId'], 'archivedWriteUp': row['archived']}
        add_writeup = to_submission_status_annotations(
            add_writeup_dict, is_private=False)
        new_status = utils.update_single_submission_status(
            status, add_writeup)
        syn.store(new_status)


def attach_writeup(syn, writeup_queueid, submission_queueid):
    '''
    Attach the write up to the submission queue

    Args:
        writeup_queueid:   Write up evaluation queue id
        submission_queueid: Submission queue id
    '''
    writeups = list(utils.evaluation_queue_query(
        syn,
        "select submitterId, entityId, archived from evaluation_{} "
        "where writeup_status == 'VALIDATED'".format(writeup_queueid)))
    submissions = list(utils.evaluation_queue_query(
        syn,
        "select objectId, submitterId from evaluation_{} "
        "where prediction_file_status == 'SCORED'".format(submission_queueid)))
    writeupsdf = pd.DataFrame(writeups)
    submissionsdf = pd.DataFrame(submissions)
    submissions_with_writeupsdf = \
        submissionsdf.merge(writeupsdf, on="submitterId", how="left")
    submissions_with_writeupsdf.apply(
        lambda row: append_writeup_to_main_submission(row, syn), axis=1)


def validate_project(syn, submission, challenge, public=False, admin=None):
    """
    Validate a Project submission.

    Args:
        submission - submission ID
        challenge - Synapse ID of Challenge wiki
        public - Project should be public (default: False)
        admin - (optional) Project should be shared with this username/ID

    Returns:
        submission_errors (str) - error messages ("" if none found)
        submission_status (str) - "VALIDATED"/"INVALID"
    """
    writeup = syn.getSubmission(submission)
    errors = []

    type_error = _validate_ent_type(writeup)
    if type_error:
        errors.append(type_error)

    contents_error = _validate_project_id(writeup, challenge)
    if contents_error:
        errors.append(contents_error)

    permissions_error = _check_project_permissions(syn, writeup, public, admin)
    errors.extend(permissions_error)

    status = "INVALID" if errors else "VALIDATED"
    return {'submission_errors': "\n".join(errors),
            "submission_status": status}


def archive_project(syn, submission, admin):
    """
    Make a copy (archive) of the Project submission.

    Args:
        submission - submission ID
        admin - user who will own the archived project
    """
    writeup = syn.getSubmission(submission)
    name = writeup.entity.name.replace("&", "+").replace("'", "")
    curr_time = int(round(time.time() * 1000))
    new_project = Project(f"Archived {name} {curr_time} {writeup.id} " +
                          f"{writeup.entityId}")
    archive = syn.store(new_project)
    permissions.set_entity_permissions(syn, archive, admin, "admin")
    archived = synapseutils.copy(syn, writeup.entityId, archive.id)
    return {"archived": archived.get(writeup.entityId)}


# TODO: move to utils module
def _validate_ent_type(submission):
    """Check entity type of submission."""

    try:
        if not isinstance(submission.entity, entity.Project):
            ent_type = re.search(
                r"entity\.(.*?)'", str(type(submission.entity))).group(1)
            return f"Submission should be a Synapse project, not a {ent_type}."
    except AttributeError:
        return "Unknown entity type; please submit a Synapse project."
    else:
        return ""


def _validate_project_id(proj, challenge):
    """Check that submission is not the Challenge site."""

    return "Submission should not be the Challenge site." \
        if proj.entityId == challenge else ""


def _validate_public_permissions(syn, proj):
    """Ensure project is shared with the public."""

    error = "Your project is not publicly available."

    try:
        # Remove error message if the project is accessible by the public.
        syn_users_perms = syn.getPermissions(
            proj.entityId, AUTHENTICATED_USERS)
        public_perms = syn.getPermissions(proj.entityId)
        if ("READ" in syn_users_perms and "DOWNLOAD" in syn_users_perms) and \
                "READ" in public_perms:
            error = ""

    except SynapseHTTPError as e:

        # Raise exception message if error is not a permissions error.
        if e.response.status_code != 403:
            raise e

    return error


def _validate_admin_permissions(syn, proj, admin):
    """Ensure project is shared with the given admin."""

    error = ("Project is private; please update its sharing settings."
             f" Writeup should be shared with {admin}.")
    try:
        # Remove error message if admin has read and download permissions.
        admin_perms = syn.getPermissions(proj.entityId, admin)
        if "READ" in admin_perms and "DOWNLOAD" in admin_perms:
            error = ""

    except SynapseHTTPError as e:

        # Raise exception message if error is not a permissions error.
        if e.response.status_code != 403:
            raise e

    return error


def _check_project_permissions(syn, submission, public, admin):
    """Check the submission sharing settings."""

    errors = []
    if public:
        public_error = _validate_public_permissions(syn, submission)
        if public_error:
            errors.append(public_error)

    if not public and admin is not None:
        admin_error = _validate_admin_permissions(syn, submission, admin)
        if admin_error:
            errors.append(admin_error)
    return errors


def validate_docker_submission(syn, submissionid):
    """Validates Synapse docker repository + sha digest submission
    This function requires users to have a synapse config file using
    synapse username and password

    Args:
        syn: Synapse connection
        submissionid: Submission id

    Returns:
        True if valid, False if not
    """
    # Uses synapse config path
    config = syn.getConfigFile(syn.configPath)
    authen = dict(config.items("authentication"))
    if authen.get("username") is None or authen.get("password") is None:
        raise ValueError('Synapse config file must have username and password')

    docker_sub = syn.getSubmission(submissionid)
    docker_repository = docker_sub.get("dockerRepositoryName")
    docker_digest = docker_sub.get("dockerDigest")
    if docker_repository is None or docker_digest is None:
        raise ValueError('Submission is not a Docker submission')
    docker_repo = docker_repository.replace("docker.synapse.org/", "")

    valid = dockertools.validate_docker(
        docker_repo=docker_repo,
        docker_digest=docker_digest,
        index_endpoint=dockertools.ENDPOINT_MAPPING['synapse'],
        username=authen['username'],
        password=authen['password']
    )
    return valid


def get_submitterid_from_submission_id(syn, submissionid, queue,
                                       verbose=False):
    """Gets submitterid from submission id

    Args:
        syn: Synapse connection
        submissionid: Submission id
        queue: Evaluation queue id
        verbose: Boolean value to print

    Returns:
        Submitter id
    """
    query = ("select submitterId from evaluation_{} "
             "where objectId == '{}'".format(queue, submissionid))
    generator = utils.evaluation_queue_query(syn, query)
    lst = list(generator)
    if not lst:
        raise ValueError('submission id {} not in queue'.format(submissionid))
    submission_dict = lst[0]
    submitterid = submission_dict['submitterId']
    if verbose:
        print("submitterid: " + submitterid)
    return submitterid


def get_submitters_lead_submission(syn, submitterid, queue,
                                   cutoff_annotation, verbose=False):
    """Gets submitter's lead submission

    Args:
        submitterid: Submitter id
        queue: Evaluation queue id
        cutoff_annotation: Boolean cutoff annotation key
        verbose: Boolean value to print

    Returns:
        previous_submission.csv or None
    """
    query = ("select objectId from evaluation_{} where submitterId == '{}' "
             "and prediction_file_status == 'SCORED' and {} == 'true' "
             "order by createdOn DESC".format(queue, submitterid,
                                              cutoff_annotation))

    generator = utils.evaluation_queue_query(syn, query)
    lst = list(generator)
    if lst:
        sub_dict = lst[0]
        objectid = sub_dict['objectId']
        if verbose:
            print("Dowloading submissionid: " + objectid)
        sub = syn.getSubmission(objectid, downloadLocation=".")
        os.rename(sub.filePath, "previous_submission.csv")
        return "previous_submission.csv"
    print("Downloading no file")
    return None


def download_current_lead_sub(syn, submissionid, status,
                              cutoff_annotation, verbose=False):
    """Download the current leading submission for boot ladder boot method

    Args:
        syn: Synapse connection
        submissionid: Submission id
        status: Submission status
        cutoff_annotation: Boolean cutoff annotation key
        verbose: Boolean value to print

    Returns:
        Path to current leading submission or None
    """
    if status == "VALIDATED":
        current_sub = syn.getSubmission(submissionid, downloadFile=False)
        queue_num = current_sub['evaluationId']
        submitterid = get_submitterid_from_submission_id(syn, submissionid,
                                                         queue_num, verbose)
        path = get_submitters_lead_submission(syn, submitterid, queue_num,
                                              cutoff_annotation, verbose)
        return path
    return None


def stop_submission_over_quota(
        syn: Synapse,
        submission_view: Union[str, SubmissionViewSchema],
        quota: int = sys.maxsize
    ):
    """Stops any submission that has exceeded the run time quota by using
    submission views.  A submission view must first exist.
    Rerunning submissions will require setting TimeRemaining annotation
    to a positive integer.

    Args:
        syn: Synapse connection
        submission_view: Submission View or its Synapse Id.
        quota: Quota in milliseconds. Default is sys.maxsize.
               One hour is 3600000.

    """
    if not isinstance(quota, int):
        raise ValueError("quota must be an integer")
    if quota <= 0:
        raise ValueError("quota must be larger than 0")

    try:
        view_query = syn.tableQuery(
            f"select {WORKFLOW_LAST_UPDATED_KEY}, {WORKFLOW_START_KEY}, id, "
            f"status from {id_of(submission_view)} where "
            "status = 'EVALUATION_IN_PROGRESS'"
        )
    except SynapseHTTPError as http_error:
        raise ValueError(
            "Submission view must have columns: "
            f"{WORKFLOW_LAST_UPDATED_KEY}, {WORKFLOW_START_KEY}, id"
        ) from http_error

    view_querydf = view_query.asDataFrame()
    runtime = (view_querydf[WORKFLOW_LAST_UPDATED_KEY] -
               view_querydf[WORKFLOW_START_KEY])
    submissions_over_quota_idx = runtime > quota
    over_quotadf = view_querydf[submissions_over_quota_idx]
    for index, row in over_quotadf.iterrows():
        add_annotations = {TIME_REMAINING_KEY: 0}
        annotations.annotate_submission(syn, row['id'], add_annotations,
                                        is_private=False, force=True)
