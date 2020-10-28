'''
Test scoring harness functions
'''
# pylint: disable=redefined-outer-name
import copy
from unittest import mock
from unittest.mock import patch

import pytest
import synapseclient

from scoring_harness import messages
from scoring_harness.queue_validator import EvaluationQueueValidator

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


@pytest.fixture
def validator():
    """Invoke validator, must patch get evaluation"""
    with patch.object(SYN, "getEvaluation", return_value=EVALUATION):
        validate = EvaluationQueueValidator(SYN, EVALUATION,
                                            admin_user_ids=[1, 3])
    return validate


def test_interact_func(validator):
    """Test not implemented error"""
    with pytest.raises(NotImplementedError):
        validator.interaction_func(SUBMISSION)


def test_valid_notify(validator):
    """Test sending validation success email"""
    with patch.object(messages, "validation_passed") as patch_send,\
         patch.object(SYN, "getUserProfile",
                      return_value=SYN_USERPROFILE) as patch_get_user:
        validator.notify(SUBMISSION, SUB_INFO)
        patch_get_user.assert_called_once_with(SUBMISSION.userId)
        patch_send.assert_called_once_with(syn=SYN,
                                           userids=[SUBMISSION.userId],
                                           acknowledge_receipt=False,
                                           dry_run=False,
                                           username=SYN_USERPROFILE.userName,
                                           queue_name=EVALUATION.name,
                                           submission_name=SUBMISSION.name,
                                           submission_id=SUBMISSION.id,
                                           challenge_synid=CHALLENGE_SYNID)


def test_error_notify(validator):
    """Test sending validation function error email"""
    info = copy.deepcopy(SUB_INFO)
    info['valid'] = False
    info['error'] = ValueError()
    with patch.object(messages, "validation_failed") as patch_send,\
         patch.object(SYN, "getUserProfile",
                      return_value=SYN_USERPROFILE) as patch_get_user:
        validator.notify(SUBMISSION, info)
        patch_get_user.assert_called_once_with(SUBMISSION.userId)
        patch_send.assert_called_once_with(syn=SYN,
                                           userids=[1, 3],
                                           send_messages=False,
                                           dry_run=False,
                                           username="Challenge Administrator",
                                           queue_name=EVALUATION.name,
                                           submission_name=SUBMISSION.name,
                                           submission_id=SUBMISSION.id,
                                           message=info['message'],
                                           challenge_synid=CHALLENGE_SYNID)


def test_invalid__notify(validator):
    """Test invalid submission email"""
    info = copy.deepcopy(SUB_INFO)
    info['valid'] = False
    info['error'] = AssertionError()
    with patch.object(messages, "validation_failed") as patch_send,\
         patch.object(SYN, "getUserProfile",
                      return_value=SYN_USERPROFILE) as patch_get_user:
        validator.notify(SUBMISSION, info)
        patch_get_user.assert_called_once_with(SUBMISSION.userId)
        patch_send.assert_called_once_with(syn=SYN,
                                           userids=[SUBMISSION.userId],
                                           send_messages=False,
                                           dry_run=False,
                                           username=SYN_USERPROFILE.userName,
                                           queue_name=EVALUATION.name,
                                           submission_name=SUBMISSION.name,
                                           submission_id=SUBMISSION.id,
                                           message=info['message'],
                                           challenge_synid=CHALLENGE_SYNID)
