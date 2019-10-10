'''
Test scoring harness functions
'''
# pylint: disable=redefined-outer-name
import copy
import mock
from mock import patch
import os
import pytest

import synapseclient

import scoring_harness.base_processor
from scoring_harness.base_processor import EvaluationQueueProcessor

SYN = mock.create_autospec(synapseclient.Synapse)
ANNOTATIONS = {'foo': 'bar'}
MESSAGE = "passed"

CHALLENGE_SYNID = "syn1234"

SUBMISSION = synapseclient.Submission(name="foo", entityId="syn123",
                                      evaluationId=2, versionNumber=1,
                                      id="syn222", filePath="foo",
                                      userId="222")
SUBMISSION_STATUS = synapseclient.SubmissionStatus(status="RECEIVED")
EVALUATION = synapseclient.Evaluation(name="foo", id="222",
                                      contentSource=CHALLENGE_SYNID)
SYN_USERPROFILE = synapseclient.UserProfile(ownerId="111", userName="foo")
BUNDLE = [(SUBMISSION, SUBMISSION_STATUS)]
SUB_INFO = {'valid': True,
            'annotations': ANNOTATIONS,
            'error': None,
            'message': MESSAGE}

@pytest.fixture
def process():
    """Invoke challenge runner"""
    processor = EvaluationQueueProcessor
    processor.syn = SYN
    processor.evaluation = EVALUATION
    processor.dry_run = False
    processor.remove_cache = False
    processor.kwargs = {}
    processor._success_status = "VALIDATED"
    return processor


def test_invalid_store_submission_status(process):
    """Storing of invalid submissions"""
    status = copy.deepcopy(SUBMISSION_STATUS)
    info = copy.deepcopy(SUB_INFO)
    info['valid'] = False
    with patch.object(scoring_harness.base_processor,
                      "update_single_submission_status",
                      return_value=status) as patch_update,\
         patch.object(SYN, "store") as patch_store:
        process.store_submission_status(process, SUBMISSION_STATUS, info)
        patch_update.assert_called_once_with(SUBMISSION_STATUS,
                                             SUB_INFO['annotations'],
                                             to_public=True)
        status.status = "INVALID"
        patch_store.assert_called_once_with(status)


def test_valid_store_submission_status(process):
    """Storing of valid submissions"""
    status = copy.deepcopy(SUBMISSION_STATUS)
    with patch.object(scoring_harness.base_processor,
                      "update_single_submission_status",
                      return_value=status) as patch_update,\
         patch.object(SYN, "store") as patch_store:
        process.store_submission_status(process, SUBMISSION_STATUS, SUB_INFO)
        patch_update.assert_called_once_with(SUBMISSION_STATUS,
                                             SUB_INFO['annotations'],
                                             to_public=True)
        status.status = process._success_status
        patch_store.assert_called_once_with(status)


def test_dryrun_store_submission_status(process):
    """Dryrun of store submission status"""
    process.dry_run=True
    status = copy.deepcopy(SUBMISSION_STATUS)
    with patch.object(scoring_harness.base_processor,
                      "update_single_submission_status",
                      return_value=status) as patch_update,\
         patch.object(SYN, "store") as patch_store:
        process.store_submission_status(process, SUBMISSION_STATUS, SUB_INFO)
        patch_update.assert_called_once_with(SUBMISSION_STATUS,
                                             SUB_INFO['annotations'],
                                             to_public=True)
        status.status = process._success_status
        patch_store.assert_not_called()


def test_abc_class(process):
    """Test ABC class"""
    with pytest.raises(TypeError, match="Can't instantiate abstract class "
                                        "EvaluationQueueProcessor with "
                                        "abstract methods interaction_func, "
                                        "notify"):
        process()


def test_valid_interact_with_submission(process):
    """No error with interaction function"""
    with patch.object(SYN, "getSubmission",
                      return_value=BUNDLE) as patch_get_bundles,\
         patch.object(process, "interaction_func",
                      return_value=SUB_INFO) as patch_interact:
        submission_info = process.interact_with_submission(process, SUBMISSION)
        assert submission_info == SUB_INFO


def test_invalid_interact_with_submission(process):
    """Raise error with interaction function"""
    with patch.object(SYN, "getSubmission",
                      return_value=BUNDLE) as patch_get_bundles,\
         patch.object(process, "interaction_func",
                      side_effect=ValueError("test")) as patch_interact:
        submission_info = process.interact_with_submission(process, SUBMISSION)
        assert not submission_info['valid']
        assert isinstance(submission_info['error'], ValueError)
        assert submission_info['message'] == 'test'
        assert submission_info['annotations'] == {}


def test_default_call(process):
    """Test call
    - get bundles
    - interact with submission
    - store submission status
    - notify
    """
    with patch.object(SYN, "getSubmissionBundles",
                      return_value=BUNDLE) as patch_get_bundles,\
         patch.object(process, "interact_with_submission",
                      return_value=SUB_INFO) as patch_interact,\
         patch.object(process, "store_submission_status") as patch_store,\
         patch.object(process, "notify") as patch_notify:
        process.__call__(process)
        patch_get_bundles.assert_called_once_with(EVALUATION,
                                                  status='RECEIVED')
        patch_interact.assert_called_once_with(SUBMISSION)
        patch_store.assert_called_once_with(SUBMISSION_STATUS, SUB_INFO)
        patch_notify.assert_called_once_with(SUBMISSION, SUB_INFO)


def test_removecache_call(process):
    """Test call
    - get bundles
    - interact with submission
    - store submission status
    - remove cache
    - notify
    """
    process.remove_cache = True

    bundle = [(SUBMISSION, SUBMISSION_STATUS)]
    with patch.object(SYN, "getSubmissionBundles",
                      return_value=bundle) as patch_get_bundles,\
         patch.object(process, "interact_with_submission",
                      return_value=SUB_INFO) as patch_interact,\
         patch.object(process, "store_submission_status") as patch_store,\
         patch.object(scoring_harness.base_processor,
                      "_remove_cached_submission") as patch_remove,\
         patch.object(process, "notify") as patch_notify:
        process.__call__(process)
        patch_get_bundles.assert_called_once_with(EVALUATION,
                                                  status='RECEIVED')
        patch_interact.assert_called_once_with(SUBMISSION)
        patch_store.assert_called_once_with(SUBMISSION_STATUS, SUB_INFO)
        patch_remove.assert_called_once_with(SUBMISSION.filePath)
        patch_notify.assert_called_once_with(SUBMISSION, SUB_INFO)


def test_dryrun_call(process):
    """Test dryrun call
    - get bundles
    - interact with submission
    - store submission status
    - remove cache
    - notify
    """
    process.dry_run = True
    bundle = [(SUBMISSION, SUBMISSION_STATUS)]
    with patch.object(SYN, "getSubmissionBundles",
                      return_value=bundle) as patch_get_bundles,\
         patch.object(process, "interact_with_submission",
                      return_value=SUB_INFO) as patch_interact,\
         patch.object(process, "store_submission_status") as patch_store,\
         patch.object(process, "notify") as patch_notify:
        process.__call__(process)
        patch_get_bundles.assert_called_once_with(EVALUATION,
                                                  status='RECEIVED')
        patch_interact.assert_called_once_with(SUBMISSION)
        patch_store.assert_called_once_with(SUBMISSION_STATUS, SUB_INFO)
        patch_notify.assert_not_called()

@pytest.mark.parametrize("valid_input", [("foo", None)])
def test_file_remove_cached_submission(valid_input):
    """Remove cache"""
    with patch.object(os, "unlink") as patch_unlink:
        scoring_harness.base_processor._remove_cached_submission(valid_input)
        patch_unlink.assert_called_once_with(valid_input)
