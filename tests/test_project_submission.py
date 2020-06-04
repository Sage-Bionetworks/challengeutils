"""Test writeup functions"""
import unittest.mock as mock
from unittest.mock import Mock, patch

import synapseclient
from synapseclient.core.exceptions import SynapseHTTPError

from challengeutils import project_submission as submission

SYN = mock.create_autospec(synapseclient.Synapse)
PROJ = mock.create_autospec(synapseclient.evaluation.Submission,
                            entityId="syn123",
                            entity=Mock(spec=synapseclient.Project))


# test that command works as expected
def test_validate_project_command_success():
    """Valid submission; status should be VALIDATED."""

    with patch.object(SYN, "getSubmission", return_value=PROJ) as patch_sub, \
            patch.object(SYN, "getPermissions") as patch_perms:
        results = submission.validate_project(SYN, patch_sub, "syn000")
        assert results.get('writeup_status') == "VALIDATED"
        assert not patch_perms.called


def test_validate_project_command_fail():
    """Invalid submission; status should be INVALID."""

    with patch.object(SYN, "getSubmission", return_value=PROJ) as patch_sub, \
            patch.object(SYN, "getPermissions") as patch_perms:
        results = submission.validate_project(SYN, patch_sub, "syn123")
        assert results.get('writeup_status') == "INVALID"
        assert not patch_perms.called


# test that only Project entity type is accepted
def test__validate_ent_type_submission_type_project():
    """Submission is a Project; no errors expected."""

    assert submission._validate_ent_type(PROJ) == ""


def test__validate_ent_type_submission_type_nonproject():
    """Submission is a File; error expected."""

    file = mock.create_autospec(synapseclient.evaluation.Submission,
                                entityId="syn123",
                                entity=synapseclient.File(path="...", parent="..."))
    assert submission._validate_ent_type(file) == \
        "Submission should be a Synapse project, not a File."


def test__validate_ent_type_submmission_type_unknown():
    """Submission is not a Synapse entity; error expected."""

    unknown = mock.create_autospec(synapseclient.evaluation.Submission,
                                   entityId="syn123",
                                   entity=Mock(),
                                   versionNumber=2)
    assert submission._validate_ent_type(unknown) == \
        "Unknown entity type; please submit a Synapse project."


# test that Challenge project is not accepted
def test__validate_project_id_nonchallenge_submission():
    """Submission is not the Challenge site; no errors expected."""

    assert submission._validate_project_id(PROJ, "syn000") == ""


def test__validate_project_id_challenge_submission():
    """Submission is the Challenge site; error expected."""

    assert submission._validate_project_id(
        PROJ, "syn123") == "Submission should not be the Challenge site."


# test private project with admin requirement
def test__validate_admin_permissions_admin_permissions_req():
    """
    Project should be shared with an admin; one call to check for
    permissions expected.
    """

    with patch.object(SYN, "getPermissions") as patch_perms:
        errors = submission._validate_admin_permissions(SYN, PROJ, admin="me")
        patch_perms.assert_called_once()

        message = ("Your private project should be shared with me. Visit "
                   "https://docs.synapse.org/articles/sharing_settings.html "
                   "for more details.")
        assert errors == message


# test private project with public requirement
def test__validate_public_permissions_public_permissions_req():
    """
    Project should be shared with the public (incl. other Synapse
    users); two calls to check for permissions expected.
    """

    with patch.object(SYN, "getPermissions") as patch_perms:
        errors = submission._validate_public_permissions(SYN, PROJ)
        assert patch_perms.call_count == 2

        message = ("Your project is not publicly available. Visit "
                   "https://docs.synapse.org/articles/sharing_settings.html "
                   "for more details.")
        assert errors == message


def test__check_project_permissions_errorcode():
    mocked_403 = SynapseHTTPError("foo", response=Mock(status_code=403))
    with patch.object(SYN, "getPermissions",
                      side_effect=mocked_403) as patch_perms:
        errors = submission._check_project_permissions(
            SYN, PROJ, public=True, admin="bob")
        assert errors == [
            "Submission is private; please update its sharing settings."]
