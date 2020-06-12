"""Test writeup functions"""
import unittest.mock as mock
from unittest.mock import Mock, patch

import pytest
import synapseclient
from synapseclient.core.exceptions import SynapseHTTPError

from challengeutils import project_submission

SYN = mock.create_autospec(synapseclient.Synapse)
PROJ = mock.create_autospec(synapseclient.evaluation.Submission,
                            entityId="syn123",
                            entity=Mock(spec=synapseclient.Project))


# test that only Project entity type is accepted
@pytest.mark.parametrize("project, output", [
    (PROJ, ""),
    (mock.create_autospec(
        synapseclient.evaluation.Submission,
        entityId="syn123", entity=synapseclient.File(
            path="...", parent="..."),
        version=1),
     "Submission should be a Synapse project, not a File."),
    (mock.create_autospec(
        synapseclient.evaluation.Submission,
        entityId="syn123",
        entity=Mock(),
        versionNumber=2),
     "Unknown entity type; please submit a Synapse project.")
])
def test__validate_ent_type_submission_type_project(project, output):
    """Submission is a Project; no errors expected."""

    assert project_submission._validate_ent_type(project) == output


# test that Challenge project is not accepted
@pytest.mark.parametrize("syn_id, output", [
    ("syn000", ""),
    ("syn123", "Submission should not be the Challenge site.")
])
def test__validate_project_id_nonchallenge_submission(syn_id, output):
    """Submission is not the Challenge site; no errors expected."""

    assert project_submission._validate_project_id(PROJ, syn_id) == output


# test private project with admin requirement
def test__validate_admin_permissions_admin_permissions_req():
    """
    Project should be shared with an admin; one call to check for
    permissions expected.
    """

    admin = "me"
    with patch.object(SYN, "getPermissions") as patch_perms:
        errors = project_submission._validate_admin_permissions(
            SYN, PROJ, admin=admin)
        patch_perms.assert_called_once()

        message = (f"Your private project should be shared with {admin}. Visit "
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
        errors = project_submission._validate_public_permissions(SYN, PROJ)
        assert patch_perms.call_count == 2

        message = ("Your project is not publicly available. Visit "
                   "https://docs.synapse.org/articles/sharing_settings.html "
                   "for more details.")
        assert errors == message


def test__check_project_permissions_errorcode():
    mocked_403 = SynapseHTTPError("foo", response=Mock(status_code=403))
    with patch.object(SYN, "getPermissions",
                      side_effect=mocked_403) as patch_perms:
        errors = project_submission._check_project_permissions(
            SYN, PROJ, public=True, admin="bob")
        assert errors == [
            "Submission is private; please update its sharing settings."]


# test that command works as expected
@pytest.mark.parametrize("syn_id, output", [
    ("syn000", "VALIDATED"),
    ("syn123", "INVALID")
])
def test_validate_project_command_success(syn_id, output):
    """Valid submission; status should be VALIDATED."""

    with patch.object(SYN, "getSubmission", return_value=PROJ) as patch_sub:
        results = project_submission.validate_project(SYN, patch_sub, syn_id)
        assert results.get('writeup_status') == output
