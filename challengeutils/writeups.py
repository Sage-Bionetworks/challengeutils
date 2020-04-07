import re
import time

import pandas as pd
from synapseclient import AUTHENTICATED_USERS, entity, Project
from synapseclient.annotations import to_submission_status_annotations
from synapseclient.exceptions import SynapseHTTPError
import synapseutils
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
        print("NO WRITEUP: " + row['team'])
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
        "select team, entityId, archived from evaluation_{} "
        "where status == 'VALIDATED'".format(writeup_queueid)))
    submissions = list(utils.evaluation_queue_query(
        syn,
        "select objectId, team from evaluation_{} "
        "where status == 'SCORED'".format(submission_queueid)))
    writeupsdf = pd.DataFrame(writeups)
    submissionsdf = pd.DataFrame(submissions)
    submissions_with_writeupsdf = \
        submissionsdf.merge(writeupsdf, on="team", how="left")

    submissions_with_writeupsdf.apply(
        lambda row: append_writeup_to_main_submission(row, syn), axis=1)


def validate_project(syn, submission, challenge, public=True, admin=None):
    """
    Validate a Project submission; errors found are returned in a dict.

    Args:
        submission - submission ID
        challenge - Synapse ID of Challenge wiki
        public - Project should be public (default: True)
        admin - (optional) Project should be shared with this username/ID
    """
    writeup = syn.getSubmission(submission)
    errors = []

    type_error = _validate_ent_type(writeup)
    if type_error:
        errors.append(type_error)

    contents_error = _validate_project_contents(writeup, challenge)
    if contents_error:
        errors.append(contents_error)

    try:
        if public:
            errors.extend(_validate_public_permissions(syn, writeup))

        if admin is not None:
            admin_error = _validate_admin_permissions(syn, writeup, admin)
            if admin_error:
                errors.append(admin_error)

    except SynapseHTTPError as e:
        if e.response.status_code == 403:
            errors.append(
                "Submission is private; please update its sharing settings.")

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
    name = writeup.name.replace("&", "+").replace("'", "")
    curr_time = int(round(time.time() * 1000))
    new_project = Project(f"Archived {name} {curr_time} {writeup.id} " +
                          f"{writeup.entityId}")
    archive = syn.store(new_project)
    permissions.set_entity_permissions(syn, archive, admin, "admin")
    synapseutils.copy(syn, writeup.entityId, archive.id)


def _validate_ent_type(ent):
    """Helper function: check entity type."""

    try:
        if not isinstance(ent.entity, entity.Project):
            ent_type = re.search(
                r"entity\.(.*?)'", str(type(ent.entity))).group(1)
            return f"Submission should be a Synapse project, not a {ent_type}."
    except AttributeError:
        return "Unknown entity type; please submit a Synapse project."
    else:
        return ""


def _validate_project_contents(proj, challenge):
    """Helper function: check that submission is not the Challenge site."""

    return "Submission should not be the Challenge site." \
        if proj.entityId == challenge else ""


def _validate_public_permissions(syn, proj):
    """Helper function: ensure project is shared with the public."""

    errors = []
    auth_perms = syn.getPermissions(proj.entityId, AUTHENTICATED_USERS)
    if "READ" not in auth_perms or "DOWNLOAD" not in auth_perms:
        errors.append("'Can download' permissions should be enabled for " +
                      "other Synapse users.")
    public_perms = syn.getPermissions(proj.entityId)
    if "READ" not in public_perms:
        errors.append("'Can view' permissions should be enabled for the " +
                      "public.")
    return errors


def _validate_admin_permissions(syn, proj, admin):
    """Helper function: ensure project is shared with the given admin."""

    admin_perms = syn.getPermissions(proj.entityId, admin)
    if "READ" not in admin_perms or "DOWNLOAD" not in admin_perms:
        return "'Can download' permissions should be enabled for " + \
            f"the admin user: {admin}"
    return ""
