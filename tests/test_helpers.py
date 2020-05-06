'''
Test challengeutils helper functions
'''
from unittest import mock
from unittest.mock import patch

import pytest
import synapseclient

from challengeutils import helpers, utils

SYN = mock.create_autospec(synapseclient.Synapse)

LAST_UPDATED_TIME = 1000000
START_TIME = 10000
DOCKER_SUB_ANNOTATION = {helpers.WORKFLOW_LAST_UPDATED_KEY: LAST_UPDATED_TIME,
                         helpers.WORKFLOW_START_KEY: START_TIME,
                         'objectId':"12345"}
EVALUATION_ID = 111


def test_noneintquota_kill_docker_submission_over_quota():
    '''
    ValueError is raised when none integer quota is passed in
    '''
    with pytest.raises(ValueError, match=r'quota must be an integer'):
        helpers.kill_docker_submission_over_quota(SYN, EVALUATION_ID,
                                                  quota="foo")


def test_greaterthan0quota_kill_docker_submission_over_quota():
    '''
    ValueError is raised when quota of 0 or less is passed
    '''
    with pytest.raises(ValueError, match=r'quota must be larger than 0'):
        helpers.kill_docker_submission_over_quota(SYN, EVALUATION_ID,
                                                  quota=0)
    with pytest.raises(ValueError, match=r'quota must be larger than 0'):
        helpers.kill_docker_submission_over_quota(SYN, EVALUATION_ID,
                                                  quota=-1)


def test_noquota_kill_docker_submission_over_quota():
    '''
    Time remaining annotation should not be added
    if no quota is set, the default is sys.maxsize.
    '''
    with patch.object(utils, "evaluation_queue_query",
                      return_value=[DOCKER_SUB_ANNOTATION]) as patch_query,\
         patch.object(SYN,
                      "getSubmissionStatus") as patch_getstatus,\
         patch.object(utils,
                      "update_single_submission_status") as patch_update, \
         patch.object(SYN, "store") as patch_synstore:
        helpers.kill_docker_submission_over_quota(SYN, EVALUATION_ID)
        query = ("select * from evaluation_{} where "
                 "status == 'EVALUATION_IN_PROGRESS'").format(EVALUATION_ID)
        patch_query.assert_called_once_with(SYN, query)
        patch_getstatus.assert_not_called()
        patch_update.assert_not_called()
        patch_synstore.assert_not_called()


def test_notdocker_kill_docker_submission_over_quota():
    '''
    Time remaining annotation should not be added
    if a submission is not validated/scored by the workflowhook
    the submission will not have the right annotations,
    '''
    with patch.object(utils, "evaluation_queue_query",
                      return_value=[{}]) as patch_query,\
         patch.object(SYN,
                      "getSubmissionStatus") as patch_getstatus,\
         patch.object(utils,
                      "update_single_submission_status") as patch_update, \
         patch.object(SYN, "store") as patch_synstore:
        helpers.kill_docker_submission_over_quota(SYN, EVALUATION_ID)
        query = ("select * from evaluation_{} where "
                 "status == 'EVALUATION_IN_PROGRESS'").format(EVALUATION_ID)
        patch_query.assert_called_once_with(SYN, query)
        patch_getstatus.assert_not_called()
        patch_update.assert_not_called()
        patch_synstore.assert_not_called()


def test_underquota_kill_docker_submission_over_quota():
    '''
    Time remaining annotation should not be added
    if the model is not over quota
    '''
    with patch.object(utils, "evaluation_queue_query",
                      return_value=[DOCKER_SUB_ANNOTATION]) as patch_query,\
         patch.object(SYN,
                      "getSubmissionStatus") as patch_getstatus,\
         patch.object(utils,
                      "update_single_submission_status") as patch_update, \
         patch.object(SYN, "store") as patch_synstore:
        # Set quota thats greater than the runtime
        quota = LAST_UPDATED_TIME - START_TIME + 9000
        helpers.kill_docker_submission_over_quota(SYN, EVALUATION_ID,
                                                  quota=quota)
        query = ("select * from evaluation_{} where "
                 "status == 'EVALUATION_IN_PROGRESS'").format(EVALUATION_ID)
        patch_query.assert_called_once_with(SYN, query)
        patch_getstatus.assert_not_called()
        patch_update.assert_not_called()
        patch_synstore.assert_not_called()


def test_overquota_kill_docker_submission_over_quota():
    '''
    Time remaining annotation should not be added
    if the model is over the quota
    '''
    sub_status = {"annotations": []}
    quota_over_annotations = {helpers.TIME_REMAINING_KEY: 0}
    with patch.object(utils, "evaluation_queue_query",
                      return_value=[DOCKER_SUB_ANNOTATION]) as patch_query,\
         patch.object(SYN, "getSubmissionStatus",
                      return_value=sub_status) as patch_getstatus,\
         patch.object(utils, "update_single_submission_status",
                      return_value=sub_status) as patch_update, \
         patch.object(SYN, "store") as patch_synstore:
        # Set quota thats lower than the runtime
        quota = LAST_UPDATED_TIME - START_TIME - 9000
        helpers.kill_docker_submission_over_quota(SYN, EVALUATION_ID,
                                                  quota=quota)
        query = ("select * from evaluation_{} where "
                 "status == 'EVALUATION_IN_PROGRESS'").format(EVALUATION_ID)
        patch_query.assert_called_once_with(SYN, query)
        objectid = DOCKER_SUB_ANNOTATION['objectId']
        patch_getstatus.assert_called_once_with(objectid)
        patch_update.assert_called_once_with(sub_status,
                                             quota_over_annotations)
        patch_synstore.assert_called_once_with(sub_status)
