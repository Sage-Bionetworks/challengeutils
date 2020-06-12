import re
import time

import pandas as pd
import synapseutils
from synapseclient import AUTHENTICATED_USERS, entity, Project
from synapseclient.annotations import to_submission_status_annotations
from synapseclient.core.exceptions import SynapseHTTPError

from . import utils
from . import permissions


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
        errors_found (dict) - error messages (empty dict if none found)
        writeup_status (str) - "VALIDATED"/"INVALID"
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
    return {'errors_found': errors, "writeup_status": status}


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

    auth_perms = syn.getPermissions(proj.entityId, AUTHENTICATED_USERS)
    public_perms = syn.getPermissions(proj.entityId)
    if ("READ" not in auth_perms or "DOWNLOAD" not in auth_perms) and \
            "READ" not in public_perms:
        return ("Your project is not publicly available. Visit "
                "https://docs.synapse.org/articles/sharing_settings.html for "
                "more details.")
    return ""


def _validate_admin_permissions(syn, proj, admin):
    """Ensure project is shared with the given admin."""

    admin_perms = syn.getPermissions(proj.entityId, admin)
    if "READ" not in admin_perms or "DOWNLOAD" not in admin_perms:
        return (f"Your private project should be shared with {admin}. Visit "
                "https://docs.synapse.org/articles/sharing_settings.html for "
                "more details.")
    return ""


def _check_project_permissions(syn, submission, public, admin):
    """Check the submission sharing settings."""

    errors = []
    try:
        if public:
            public_error = _validate_public_permissions(syn, submission)
            if public_error:
                errors.append(public_error)

        if admin is not None:
            admin_error = _validate_admin_permissions(syn, submission, admin)
            if admin_error:
                errors.append(admin_error)

    except SynapseHTTPError as e:
        if e.response.status_code == 403:
            errors.append(
                "Submission is private; please update its sharing settings.")
        else:
            raise e
    return errors
