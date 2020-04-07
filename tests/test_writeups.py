"""Test writeup functions"""
import unittest.mock as mock
from unittest.mock import Mock, patch

import synapseclient

from challengeutils import writeups

SYN = mock.create_autospec(synapseclient.Synapse)
PROJ = mock.create_autospec(synapseclient.evaluation.Submission,
                            entityId="syn123",
                            entity=Mock(spec=synapseclient.Project))


# test that command works as expected
def test_command_success():
    with patch.object(SYN, "getSubmission", return_value=PROJ) as patch_sub, \
            patch.object(SYN, "getPermissions") as patch_perms:
        results = writeups.validate_project(SYN, patch_sub, "syn000")
        assert results.get('writeup_status') == "VALIDATED"
        assert not patch_perms.called


def test_command_fail():
    with patch.object(SYN, "getSubmission", return_value=PROJ) as patch_sub, \
            patch.object(SYN, "getPermissions") as patch_perms:
        results = writeups.validate_project(SYN, patch_sub, "syn123")
        assert results.get('writeup_status') == "INVALID"
        assert not patch_perms.called


# test that only Project entity type is accepted
def test_submission_type_project():
    assert writeups._validate_ent_type(PROJ) == ""


def test_submission_type_nonproject():
    file = mock.create_autospec(synapseclient.evaluation.Submission,
                                entityId="syn123",
                                entity=synapseclient.File(path="...", parent="..."))
    assert writeups._validate_ent_type(file) == \
        "Submission should be a Synapse project, not a File."


def test_submmission_type_unknown():
    unknown = mock.create_autospec(synapseclient.evaluation.Submission,
                                   entityId="syn123",
                                   entity=Mock())
    assert writeups._validate_ent_type(unknown) == \
        "Unknown entity type; please submit a Synapse project."


# test that Challenge project is not accepted
def test_validate_nonchallenge_submission():
    assert writeups._validate_project_contents(
        PROJ, "syn000") == ""


def test_validate_challenge_submission():
    assert writeups._validate_project_contents(
        PROJ, "syn123") == "Submission should not be the Challenge site."


# test private project with admin requirement
def test_validate_permissions_admin():
    with patch.object(SYN, "getPermissions") as patch_perms:
        writeups._validate_admin_permissions(SYN, PROJ, admin="me")
        patch_perms.assert_called_once()


# test private project with public requirement
def test_validate_permissions_public():
    with patch.object(SYN, "getPermissions") as patch_perms:
        writeups._validate_public_permissions(SYN, PROJ)
        assert patch_perms.call_count == 2


# test semi-private project with public requirement
def test_validate_permissions_both():
    with patch.object(SYN, "getPermissions") as patch_perms:
        writeups._validate_public_permissions(SYN, PROJ)
        writeups._validate_admin_permissions(SYN, PROJ, admin="me")
        assert patch_perms.call_count == 3


# TODO: add tests for actual permission errors?
