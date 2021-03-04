"""Test writeup functions"""
import os
import tempfile
import unittest.mock as mock
from unittest.mock import Mock, patch
import uuid

import pandas as pd
import pytest
import synapseclient
from synapseclient.core.exceptions import SynapseHTTPError

from challengeutils import annotations, dockertools, submission, utils

SYN = mock.create_autospec(synapseclient.Synapse)
SYN.configPath = None
PROJ = mock.create_autospec(synapseclient.evaluation.Submission,
                            entityId="syn123",
                            entity=Mock(spec=synapseclient.Project))
SUBMISSIONID = "111"
QUEUEID = "333"


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
    """Tests that only a Project submission is accepted."""
    assert submission._validate_ent_type(project) == output


@pytest.mark.parametrize("syn_id, output", [
    ("syn000", ""),
    ("syn123", "Submission should not be the Challenge site.")
])
def test__validate_project_id_nonchallenge_submission(syn_id, output):
    """Tests that project ID is not the Challenge project ID."""
    assert submission._validate_project_id(PROJ, syn_id) == output


def test__validate_admin_permissions_admin_permissions_req():
    """Tests sharing settings for an admin.

    One call to check for permissions expected.
    """
    admin = "me"
    with patch.object(SYN, "getPermissions") as patch_perms:
        errors = submission._validate_admin_permissions(
            SYN, PROJ, admin=admin)
        patch_perms.assert_called_once()

        message = ("Project is private; please update its sharing settings."
                   f" Writeup should be shared with {admin}.")
        assert errors == message


def test__validate_public_permissions_public_permissions_req():
    """Tests sharing settings to the public.

    Two calls to check for permissions expected (one for all Synapse
    users, another for the public).
    """
    with patch.object(SYN, "getPermissions") as patch_perms:
        errors = submission._validate_public_permissions(SYN, PROJ)
        assert patch_perms.call_count == 2
        assert errors == "Your project is not publicly available."


@pytest.mark.parametrize("public, admin, output", [
    (True, None, "Your project is not publicly available."),
    (True, "me", "Your project is not publicly available."),
    (False, "me", ("Project is private; please update its sharing settings."
                   " Writeup should be shared with me."))
])
def test__check_project_permissions_errorcode(public, admin, output):
    """Tests that exception is thrown when project is private.

    If project is private, but is expected to be accessible by the public
    or an admin user/team, then exception should be thrown. If both flags
    are given, then `public` error message should take precedence.
    """
    mocked_403 = SynapseHTTPError("foo", response=Mock(status_code=403))
    with patch.object(SYN, "getPermissions",
                      side_effect=mocked_403) as patch_perms:
        errors = submission._check_project_permissions(
            SYN, PROJ, public=public, admin=admin)
        assert errors == [output]


@pytest.mark.parametrize("syn_id, output", [
    ("syn000", "VALIDATED"),
    ("syn123", "INVALID")
])
def test_validate_project_command_success(syn_id, output):
    """Tests that overall functionality works."""
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


def test_nosub_get_submitterid_from_submission_id():
    """Tests if submission id doesn't exist"""
    with pytest.raises(ValueError,
                       match=r'submission id*'),\
        patch.object(utils, "evaluation_queue_query",
                     return_value=[]) as patch_query:
        submission.get_submitterid_from_submission_id(SYN, SUBMISSIONID,
                                                      QUEUEID, verbose=False)
        patch_query.assert_called_once()


def test_get_submitterid_from_submission_id():
    """Tests getting of submitter id"""
    with patch.object(utils, "evaluation_queue_query",
                      return_value=[{'submitterId': 1}]) as patch_query:
        submitter = submission.get_submitterid_from_submission_id(
            SYN, SUBMISSIONID, QUEUEID, verbose=False
        )
        patch_query.assert_called_once()
        assert submitter == 1


def test_get_submitters_lead_submission():
    """Tests getting of lead submission"""
    sub = synapseclient.Submission(evaluationId='2', entityId='2',
                                   versionNumber='3')
    temp = tempfile.NamedTemporaryFile()
    sub.filePath = temp.name

    with patch.object(utils, "evaluation_queue_query",
                      return_value=[{'objectId': 1}]) as patch_query,\
        patch.object(SYN, "getSubmission",
                     return_value=sub) as patch_getsub:
        dl_file = submission.get_submitters_lead_submission(
            SYN, SUBMISSIONID, QUEUEID, "key", verbose=False
        )
        patch_query.assert_called_once()
        patch_getsub.assert_called_once_with(1, downloadLocation='.')
        assert dl_file == "previous_submission.csv"
        os.unlink("previous_submission.csv")


def test_none_get_submitters_lead_submission():
    """Tests not getting submission"""
    with patch.object(utils, "evaluation_queue_query",
                      return_value=[]) as patch_query:
        dl_file = submission.get_submitters_lead_submission(
            SYN, SUBMISSIONID, QUEUEID, "key", verbose=False
        )
        patch_query.assert_called_once()
        assert dl_file is None


def test_download_current_lead_sub():
    """Tests download of lead submission"""
    sub = synapseclient.Submission(evaluationId='2', entityId='2',
                                   versionNumber='3')
    with patch.object(SYN, "getSubmission",
                      return_value=sub) as patch_getsub,\
        patch.object(submission, "get_submitterid_from_submission_id",
                     return_value="2") as patch_getsubmitter,\
        patch.object(submission, "get_submitters_lead_submission",
                     return_value="path") as patch_get_lead:
        dl_file = submission.download_current_lead_sub(
            SYN, SUBMISSIONID, "VALIDATED", "key", verbose=False
        )
        patch_getsubmitter.assert_called_once()
        patch_get_lead.assert_called_once()
        assert dl_file == "path"


def test_invalid_download_current_lead_sub():
    """Tests None is downloaded if status is INVALID"""
    dl_file = submission.download_current_lead_sub(
        SYN, SUBMISSIONID, "INVALID", "key", verbose=False
    )
    assert dl_file is None


class TestStopDockerSubmission():
    def setup_method(self):
        self.last_updated_time = 1000000
        self.start_time = 10000
        self.submission_viewdf = pd.DataFrame([{
            submission.WORKFLOW_LAST_UPDATED_KEY: self.last_updated_time,
            submission.WORKFLOW_START_KEY: self.start_time,
            'id': "12345"
        }])
        self.mock_tablequery = Mock()
        self.fileview_id = 111

    def test_noneintquota(self):
        '''
        ValueError is raised when none integer quota is passed in
        '''
        with pytest.raises(ValueError, match=r'quota must be an integer'):
            submission.stop_submission_over_quota(SYN, self.fileview_id,
                                                  quota="foo")

    @pytest.mark.parametrize("quota", [0, -1])
    def test_greaterthan0quota(self, quota):
        '''
        ValueError is raised when quota of 0 or less is passed
        '''
        with pytest.raises(ValueError, match=r'quota must be larger than 0'):
            submission.stop_submission_over_quota(SYN, self.fileview_id,
                                                  quota=quota)

    def test_queryfail(self):
        '''
        ValueError is raised tableQuery fails
        '''
        with patch.object(SYN, "tableQuery",
                          side_effect=SynapseHTTPError),\
             pytest.raises(ValueError,
                           match=r'Submission view must have columns:*'):
            submission.stop_submission_over_quota(SYN, self.fileview_id)

    def test_noquota(self):
        '''
        Time remaining annotation should not be added
        if no quota is set, the default is sys.maxsize.
        '''
        with patch.object(SYN, "tableQuery",
                          return_value=self.mock_tablequery) as patch_query,\
             patch.object(self.mock_tablequery, "asDataFrame",
                          return_value=self.submission_viewdf),\
             patch.object(annotations, "annotate_submission") as patch_store:
            submission.stop_submission_over_quota(SYN, self.fileview_id)
            query = (
                f"select {submission.WORKFLOW_LAST_UPDATED_KEY}, "
                f"{submission.WORKFLOW_START_KEY}, id, "
                f"status from {self.fileview_id} where "
                "status = 'EVALUATION_IN_PROGRESS'"
            )
            patch_query.assert_called_once_with(query)
            patch_store.assert_not_called()

    def test_notstartedsubmission(self):
        '''
        Time remaining annotation should not be added
        if a submission is not validated/scored by the workflowhook
        the submission will not have the right annotations,
        '''
        self.submission_viewdf.loc[
            0, submission.WORKFLOW_LAST_UPDATED_KEY
        ] = float('nan')
        with patch.object(SYN, "tableQuery",
                          return_value=self.mock_tablequery) as patch_query,\
             patch.object(self.mock_tablequery, "asDataFrame",
                          return_value=self.submission_viewdf),\
             patch.object(annotations, "annotate_submission") as patch_store:
            submission.stop_submission_over_quota(SYN, self.fileview_id)
            query = (
                f"select {submission.WORKFLOW_LAST_UPDATED_KEY}, "
                f"{submission.WORKFLOW_START_KEY}, id, "
                f"status from {self.fileview_id} where "
                "status = 'EVALUATION_IN_PROGRESS'"
            )
            patch_query.assert_called_once_with(query)
            patch_store.assert_not_called()

    def test_underquota(self):
        '''
        Time remaining annotation should not be added
        if the model is not over quota
        '''
        with patch.object(SYN, "tableQuery",
                          return_value=self.mock_tablequery) as patch_query,\
             patch.object(self.mock_tablequery, "asDataFrame",
                          return_value=self.submission_viewdf),\
             patch.object(annotations, "annotate_submission") as patch_store:
            quota = self.last_updated_time - self.start_time + 9000
            submission.stop_submission_over_quota(SYN, self.fileview_id,
                                                  quota=quota)
            query = (
                f"select {submission.WORKFLOW_LAST_UPDATED_KEY}, "
                f"{submission.WORKFLOW_START_KEY}, id, "
                f"status from {self.fileview_id} where "
                "status = 'EVALUATION_IN_PROGRESS'"
            )
            patch_query.assert_called_once_with(query)
            patch_store.assert_not_called()

    def test_overquota(self):
        '''
        Time remaining annotation should not be added
        if the model is over the quota
        '''
        with patch.object(SYN, "tableQuery",
                          return_value=self.mock_tablequery) as patch_query,\
             patch.object(self.mock_tablequery, "asDataFrame",
                          return_value=self.submission_viewdf),\
             patch.object(annotations, "annotate_submission") as patch_store:
            quota = self.last_updated_time - self.start_time - 9000
            submission.stop_submission_over_quota(SYN, self.fileview_id,
                                                  quota=quota)
            query = (
                f"select {submission.WORKFLOW_LAST_UPDATED_KEY}, "
                f"{submission.WORKFLOW_START_KEY}, id, "
                f"status from {self.fileview_id} where "
                "status = 'EVALUATION_IN_PROGRESS'"
            )
            patch_query.assert_called_once_with(query)
            patch_store.assert_called_once_with(
                SYN, "12345", {submission.TIME_REMAINING_KEY: 0},
                is_private=False, force=True
            )
