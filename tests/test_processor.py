'''
Test scoring harness functions
'''
# pylint: disable=redefined-outer-name
import copy
import os
from unittest import mock
from unittest.mock import patch

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
SUBMISSION_STATUS = synapseclient.SubmissionStatus(status="RECEIVED", id="111", etag="222")
EVALUATION = synapseclient.Evaluation(name="foo", id="222",
                                      contentSource=CHALLENGE_SYNID)
SYN_USERPROFILE = synapseclient.UserProfile(ownerId="111", userName="foo")
BUNDLE = [(SUBMISSION, SUBMISSION_STATUS)]
SUB_INFO = {'valid': True,
            'annotations': ANNOTATIONS,
            'error': None,
            'message': MESSAGE}


class Processor(EvaluationQueueProcessor):
    """Create class that extends ABCmeta class"""
    _success_status = "VALIDATED"

    def __init__(self, syn, evaluation, admin_user_ids=None, dry_run=False,
                 remove_cache=False, **kwargs):
        EvaluationQueueProcessor.__init__(self, syn, evaluation,
                                          admin_user_ids=admin_user_ids,
                                          dry_run=dry_run,
                                          remove_cache=remove_cache, **kwargs)

    def interaction_func(self, submission, **kwargs):
        pass

    def notify(self, submission, submission_info):
        pass


def test_abc_class():
    """Test ABC class"""
    with pytest.raises(TypeError, match="Can't instantiate abstract class "
                                        "EvaluationQueueProcessor with "
                                        "abstract methods interaction_func, "
                                        "notify"):
        EvaluationQueueProcessor(SYN, EVALUATION)


def test_init():
    """Test default initialization"""
    with patch.object(SYN, "getEvaluation",
                      return_value=EVALUATION) as patch_get_eval,\
         patch.object(SYN, "getUserProfile",
                      return_value={'ownerId': 1111}) as patch_getuser:
        proc = Processor(SYN, EVALUATION.id)
        patch_get_eval.assert_called_once_with(EVALUATION.id)
        patch_getuser.assert_called_once_with()
        assert proc.admin_user_ids == [1111]
        assert not proc.dry_run
        assert not proc.remove_cache


def test_specifyadmin_init():
    """Test specify parameters initialization"""
    with patch.object(SYN, "getEvaluation",
                      return_value=EVALUATION) as patch_get_eval,\
         patch.object(SYN, "getUserProfile") as patch_getuser:
        proc = Processor(SYN, EVALUATION, admin_user_ids=[1, 3],
                         dry_run=True, remove_cache=True,
                         foo="bar", doo="doo")
        patch_get_eval.assert_called_once_with(EVALUATION)
        patch_getuser.assert_not_called()
        assert proc.admin_user_ids == [1, 3]
        assert proc.dry_run
        assert proc.remove_cache
        assert proc.kwargs == {'foo': 'bar', 'doo': 'doo'}


@pytest.fixture
def processor():
    """Invoke processor, must patch get evaluation"""
    with patch.object(SYN, "getEvaluation", return_value=EVALUATION):
        process = Processor(SYN, EVALUATION)
    return process


def test_invalid_store_submission_status(processor):
    """Storing of invalid submissions"""
    status = copy.deepcopy(SUBMISSION_STATUS)
    info = copy.deepcopy(SUB_INFO)
    info['valid'] = False
    with patch.object(scoring_harness.base_processor,
                      "update_single_submission_status",
                      return_value=status) as patch_update,\
         patch.object(SYN, "store") as patch_store:
        processor.store_submission_status(SUBMISSION_STATUS, info)
        patch_update.assert_called_once_with(SUBMISSION_STATUS,
                                             SUB_INFO['annotations'],
                                             is_private=False)
        status.status = "INVALID"
        patch_store.assert_called_once_with(status)


def test_valid_store_submission_status(processor):
    """Storing of valid submissions"""
    status = copy.deepcopy(SUBMISSION_STATUS)
    with patch.object(scoring_harness.base_processor,
                      "update_single_submission_status",
                      return_value=status) as patch_update,\
         patch.object(SYN, "store") as patch_store:
        processor.store_submission_status(SUBMISSION_STATUS, SUB_INFO)
        patch_update.assert_called_once_with(SUBMISSION_STATUS,
                                             SUB_INFO['annotations'],
                                             is_private=False)
        status.status = processor._success_status
        patch_store.assert_called_once_with(status)


def test_dryrun_store_submission_status(processor):
    """Dryrun of store submission status"""
    processor.dry_run = True
    status = copy.deepcopy(SUBMISSION_STATUS)
    with patch.object(scoring_harness.base_processor,
                      "update_single_submission_status",
                      return_value=status) as patch_update,\
         patch.object(SYN, "store") as patch_store:
        processor.store_submission_status(SUBMISSION_STATUS, SUB_INFO)
        patch_update.assert_called_once_with(SUBMISSION_STATUS,
                                             SUB_INFO['annotations'],
                                             is_private=False)
        status.status = processor._success_status
        patch_store.assert_not_called()


def test_valid_interact_with_submission(processor):
    """No error with interaction function"""
    with patch.object(SYN, "getSubmission",
                      return_value=BUNDLE) as patch_get_bundles,\
         patch.object(processor, "interaction_func",
                      return_value=SUB_INFO) as patch_interact:
        submission_info = processor.interact_with_submission(SUBMISSION)
        assert submission_info == SUB_INFO


def test_invalid_interact_with_submission(processor):
    """Raise error with interaction function"""
    with patch.object(SYN, "getSubmission",
                      return_value=BUNDLE) as patch_get_bundles,\
         patch.object(processor, "interaction_func",
                      side_effect=ValueError("test")) as patch_interact:
        submission_info = processor.interact_with_submission(SUBMISSION)
        assert not submission_info['valid']
        assert isinstance(submission_info['error'], ValueError)
        assert submission_info['message'] == 'test'
        assert submission_info['annotations'] == {}


def test_default_call(processor):
    """Test call
    - get bundles
    - interact with submission
    - store submission status
    - notify
    """
    with patch.object(SYN, "getSubmissionBundles",
                      return_value=BUNDLE) as patch_get_bundles,\
         patch.object(processor, "interact_with_submission",
                      return_value=SUB_INFO) as patch_interact,\
         patch.object(processor, "store_submission_status") as patch_store,\
         patch.object(processor, "notify") as patch_notify:
        processor()
        patch_get_bundles.assert_called_once_with(EVALUATION,
                                                  status='RECEIVED')
        patch_interact.assert_called_once_with(SUBMISSION)
        patch_store.assert_called_once_with(SUBMISSION_STATUS, SUB_INFO)
        patch_notify.assert_called_once_with(SUBMISSION, SUB_INFO)


def test_removecache_call(processor):
    """Test call
    - get bundles
    - interact with submission
    - store submission status
    - remove cache
    - notify
    """
    processor.remove_cache = True

    bundle = [(SUBMISSION, SUBMISSION_STATUS)]
    with patch.object(SYN, "getSubmissionBundles",
                      return_value=bundle) as patch_get_bundles,\
         patch.object(processor, "interact_with_submission",
                      return_value=SUB_INFO) as patch_interact,\
         patch.object(processor, "store_submission_status") as patch_store,\
         patch.object(scoring_harness.base_processor,
                      "_remove_cached_submission") as patch_remove,\
         patch.object(processor, "notify") as patch_notify:
        processor()
        patch_get_bundles.assert_called_once_with(EVALUATION,
                                                  status='RECEIVED')
        patch_interact.assert_called_once_with(SUBMISSION)
        patch_store.assert_called_once_with(SUBMISSION_STATUS, SUB_INFO)
        patch_remove.assert_called_once_with(SUBMISSION.filePath)
        patch_notify.assert_called_once_with(SUBMISSION, SUB_INFO)


def test_dryrun_call(processor):
    """Test dryrun call
    - get bundles
    - interact with submission
    - store submission status
    - remove cache
    - notify
    """
    processor.dry_run = True
    bundle = [(SUBMISSION, SUBMISSION_STATUS)]
    with patch.object(SYN, "getSubmissionBundles",
                      return_value=bundle) as patch_get_bundles,\
         patch.object(processor, "interact_with_submission",
                      return_value=SUB_INFO) as patch_interact,\
         patch.object(processor, "store_submission_status") as patch_store,\
         patch.object(processor, "notify") as patch_notify:
        processor()
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
