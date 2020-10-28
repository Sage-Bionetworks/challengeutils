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
from scoring_harness.queue_scorer import EvaluationQueueScorer

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
def scorer():
    """Invoke validator, must patch get evaluation"""
    with patch.object(SYN, "getEvaluation", return_value=EVALUATION),\
         patch.object(SYN, "getUserProfile", return_value={'ownerId': 111}):
        score = EvaluationQueueScorer(SYN, EVALUATION)
    return score


def test_interact_func(scorer):
    """Test not implemented error"""
    with pytest.raises(NotImplementedError):
        scorer.interaction_func(SUBMISSION)


def test_valid_notify(scorer):
    """Test sending validation success email"""
    with patch.object(messages, "scoring_succeeded") as patch_send,\
         patch.object(SYN, "getUserProfile",
                      return_value=SYN_USERPROFILE) as patch_get_user:
        scorer.notify(SUBMISSION, SUB_INFO)
        patch_get_user.assert_called_once_with(SUBMISSION.userId)
        patch_send.assert_called_once_with(syn=SYN,
                                           userids=[SUBMISSION.userId],
                                           send_messages=False,
                                           dry_run=False,
                                           message=SUB_INFO['message'],
                                           username=SYN_USERPROFILE.userName,
                                           queue_name=EVALUATION.name,
                                           submission_name=SUBMISSION.name,
                                           submission_id=SUBMISSION.id,
                                           challenge_synid=CHALLENGE_SYNID)


def test_error_notify(scorer):
    """Test sending validation function error email"""
    info = copy.deepcopy(SUB_INFO)
    info['valid'] = False
    with patch.object(messages, "scoring_error") as patch_send,\
         patch.object(SYN, "getUserProfile",
                      return_value=SYN_USERPROFILE) as patch_get_user:
        scorer.notify(SUBMISSION, info)
        patch_get_user.assert_called_once_with(SUBMISSION.userId)
        patch_send.assert_called_once_with(syn=SYN,
                                           userids=[111],
                                           send_messages=False,
                                           dry_run=False,
                                           message=info['message'],
                                           username="Challenge Administrator",
                                           queue_name=EVALUATION.name,
                                           submission_name=SUBMISSION.name,
                                           submission_id=SUBMISSION.id,
                                           challenge_synid=CHALLENGE_SYNID)
