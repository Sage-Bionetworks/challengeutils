"""Test writeup functions"""
import unittest.mock as mock
from unittest.mock import Mock, patch
import uuid

import pytest
import synapseclient
from synapseclient.core.exceptions import SynapseHTTPError

from challengeutils import dockertools, submission

SYN = mock.create_autospec(synapseclient.Synapse)
SYN.configPath = None
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

    assert submission._validate_ent_type(project) == output


# test that Challenge project is not accepted
@pytest.mark.parametrize("syn_id, output", [
    ("syn000", ""),
    ("syn123", "Submission should not be the Challenge site.")
])
def test__validate_project_id_nonchallenge_submission(syn_id, output):
    """Submission is not the Challenge site; no errors expected."""

    assert submission._validate_project_id(PROJ, syn_id) == output


# test private project with admin requirement
def test__validate_admin_permissions_admin_permissions_req():
    """
    Project should be shared with an admin; one call to check for
    permissions expected.
    """

    admin = "me"
    with patch.object(SYN, "getPermissions") as patch_perms:
        errors = submission._validate_admin_permissions(
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


# test that command works as expected
@pytest.mark.parametrize("syn_id, output", [
    ("syn000", "VALIDATED"),
    ("syn123", "INVALID")
])
def test_validate_project_command_success(syn_id, output):
    """Valid submission; status should be VALIDATED."""

    with patch.object(SYN, "getSubmission", return_value=PROJ) as patch_sub:
        results = submission.validate_project(SYN, patch_sub, syn_id)
        assert results.get('submission_status') == output


def test_validate_docker_submission_valid():
    """Tests that True is returned when validate docker
    submission is valid"""
    config = Mock()
    docker_repo = 'docker.synapse.org/syn1234/docker_repo'
    docker_digest = 'sha123566'
    username = str(uuid.uuid1())
    password = str(uuid.uuid1())
    docker_sub = synapseclient.Submission(evaluationId=1,
                                          entityId=1,
                                          versionNumber=2,
                                          dockerRepositoryName=docker_repo,
                                          dockerDigest=docker_digest)
    with patch.object(SYN, "getConfigFile", return_value=config),\
         patch.object(config, "items",
                      return_value={'username': username,
                                    'password': password}),\
         patch.object(SYN, "getSubmission",
                      return_value=docker_sub) as patch_get_sub,\
         patch.object(dockertools, "validate_docker",
                      return_value=True) as patch_validate:
        valid = submission.validate_docker_submission(SYN, "123455")
        patch_validate.assert_called_once_with(
            docker_repo="syn1234/docker_repo",
            docker_digest=docker_digest,
            index_endpoint=dockertools.ENDPOINT_MAPPING['synapse'],
            username=username,
            password=password
        )
        patch_get_sub.assert_called_once_with("123455")
        assert valid


def test_validate_docker_submission_nousername():
    """Tests ValueError is thrown when no username or password is passed"""
    config = Mock()
    password = str(uuid.uuid1())
    with patch.object(SYN, "getConfigFile", return_value=config),\
         patch.object(config, "items",
                      return_value={'username': None,
                                    'password': password}),\
         pytest.raises(ValueError,
                       match='Synapse config file must have username '
                             'and password'):
        submission.validate_docker_submission(SYN, "123455")


def test_validate_docker_submission_notdocker():
    """Tests ValueError is thrown when submission is not docker submission"""
    config = Mock()
    docker_repo = 'docker.synapse.org/syn1234/docker_repo'
    docker_digest = None
    username = str(uuid.uuid1())
    password = str(uuid.uuid1())
    docker_sub = synapseclient.Submission(evaluationId=1,
                                          entityId=1,
                                          versionNumber=2,
                                          dockerRepositoryName=docker_repo,
                                          dockerDigest=docker_digest)
    with patch.object(SYN, "getConfigFile", return_value=config),\
         patch.object(config, "items",
                      return_value={'username': username,
                                    'password': password}),\
         patch.object(SYN, "getSubmission",
                      return_value=docker_sub),\
         pytest.raises(ValueError,
                       match='Submission is not a Docker submission'):
        submission.validate_docker_submission(SYN, "123455")
