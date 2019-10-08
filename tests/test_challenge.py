'''
Test scoring harness functions
'''
# pylint: disable=redefined-outer-name
import mock
from mock import patch
import pytest
import synapseclient
import scoring_harness.challenge
from scoring_harness.challenge import Challenge
from scoring_harness import messages
# from scoring_harness.challenge import score_single_submission
# from scoring_harness.challenge import score
# from scoring_harness.challenge import validate_single_submission
# from scoring_harness.challenge import validate

SYN = mock.create_autospec(synapseclient.Synapse)
SCORES = {"score": 5}
MESSAGE = "passed"
ERROR_MESSAGE = "error for days"

@pytest.fixture
def challenge_runner():
    """Invoke challenge runner"""
    challenge_run = Challenge(SYN, dry_run=False, send_messages=False,
                              acknowledge_receipt=False, remove_cache=False)
    return challenge_run


def validation_func(path, truth):
    """Test validation function"""
    return(True, MESSAGE)


def scoring_func(path, truth):
    """Test scoring function"""
    return(SCORES, MESSAGE)


def invalid_func(path, truth):
    """Test invalid function"""
    raise ValueError(ERROR_MESSAGE)


QUEUE_INFO_DICT = {'id': '1',
                   'scoring_func': scoring_func,
                   'goldstandard_path': "./",
                   'validation_func': validation_func}
SUBMISSION = synapseclient.Submission(
    name="foo", entityId="syn123", evaluationId=2, versionNumber=1,
    id="syn222", filePath="foo", userId="222")
EVALUATION = synapseclient.Evaluation(
    name="foo", id="222", contentSource="syn12")
SYN_USERPROFILE = synapseclient.UserProfile(ownerId="111")


def test_score_single_submission(challenge_runner):
    """Test scoring of single submission"""
    challenge_runner.dry_run = True
    status = synapseclient.SubmissionStatus(status="VALIDATED")
    status, message = challenge_runner.score_single_submission(
        SUBMISSION, status, scoring_func, "path")
    expected_status = {
        "annotations": {
            "longAnnos": [{
                "isPrivate": True,
                "key": "score",
                "value": 5
            }]
        },
        "status": "SCORED"
    }
    assert status == expected_status
    assert message == "passed"


def test_storestatus_score_single_submission(challenge_runner):
    '''
    Test storing of status
    '''
    expected_status = {
        "annotations": {
            "longAnnos": [{
                "isPrivate": True,
                "key": "score",
                "value": 5
            }]
        },
        "status": "SCORED"
    }
    store_return = "return me"
    status = synapseclient.SubmissionStatus(status="VALIDATED")
    with patch.object(SYN, "store",
                      return_value=store_return) as patch_store:
        status, message = challenge_runner.score_single_submission(
            SUBMISSION, status, scoring_func, "path")
        patch_store.assert_called_once_with(expected_status)
        # Return the stored status
        assert status == store_return
        assert message == MESSAGE


def test_invalid_score_single_submission(challenge_runner):
    '''
    Test invalid submission
    '''
    challenge_runner.dry_run = True
    status = synapseclient.SubmissionStatus(status="VALIDATED")
    status, message = challenge_runner.score_single_submission(
        SUBMISSION, status,
        invalid_func, "path")
    assert status == {'status': 'INVALID'}
    assert message == ERROR_MESSAGE


def test_score(challenge_runner):
    '''
    Test score process
    - get evaluation
    - get bundles
    - get submission
    - score single submission
    - get users
    - send emails
    '''
    status = synapseclient.SubmissionStatus(status="SCORED")

    with patch.object(SYN, "getEvaluation",
                      return_value=EVALUATION) as patch_getevaluation,\
         patch.object(SYN, "getSubmissionBundles",
                      return_value=[(SUBMISSION, status)]) as patch_get_bundles,\
         patch.object(SYN, "getSubmission",
                      return_value=SUBMISSION) as patch_get_sub,\
         patch.object(Challenge, "score_single_submission",
                      return_value=(status, "message")) as patch_score_single,\
         patch.object(SYN, "getUserProfile",
                      return_value=SYN_USERPROFILE) as patch_get_user,\
         patch.object(messages, "scoring_succeeded") as patch_send,\
         patch.object(scoring_harness.challenge, "get_user_name",
                      return_value="foo") as patch_get_user_name:
        challenge_runner.score(QUEUE_INFO_DICT,
                               [1],
                               "syn1234",
                               status='VALIDATED')
        patch_getevaluation.assert_called_once_with(QUEUE_INFO_DICT['id'])
        patch_get_bundles.assert_called_once_with(
            EVALUATION, status='VALIDATED')
        patch_get_sub.assert_called_once_with(SUBMISSION)
        patch_score_single.assert_called_once_with(
            SUBMISSION, status,
            scoring_func, QUEUE_INFO_DICT['goldstandard_path'])
        patch_get_user.assert_called_once_with(SUBMISSION.userId)
        patch_send.assert_called_once_with(syn=SYN,
                                           userids=[SUBMISSION.userId],
                                           send_messages=False,
                                           dry_run=False,
                                           message="message",
                                           username="foo",
                                           queue_name=EVALUATION.name,
                                           submission_name=SUBMISSION.name,
                                           submission_id=SUBMISSION.id,
                                           challenge_synid="syn1234")
        patch_get_user_name.assert_called_once_with(SYN_USERPROFILE)


def test_valid_validate_single_submission(challenge_runner):
    '''
    Test validation of single valid submission
    '''
    challenge_runner.dry_run = True
    status = synapseclient.SubmissionStatus(status="VALIDATED")
    valid, error, message = challenge_runner.validate_single_submission(
        SUBMISSION, status, validation_func, "path")
    assert valid
    assert error is None
    assert message == MESSAGE


def test_storestatus_validate_single_submission(challenge_runner):
    '''
    Test storing of status
    '''
    status = synapseclient.SubmissionStatus(status="VALIDATED")
    with patch.object(SYN, "store") as patch_store:
        status = synapseclient.SubmissionStatus(status="VALIDATED")
        valid, error, message = challenge_runner.validate_single_submission(
            SUBMISSION, status, validation_func, "path")
        expected_status = {
            "annotations": {
                'stringAnnos': [{
                    "isPrivate": False,
                    "key": "FAILURE_REASON",
                    "value": ''
                }]
            },
            "status": "VALIDATED"
        }
        assert valid
        assert error is None
        assert message == MESSAGE
        patch_store.assert_called_once_with(expected_status)


def test_invalid_validate_single_submission(challenge_runner):
    '''
    Test invalid submission
    '''
    challenge_runner.dry_run = True
    status = synapseclient.SubmissionStatus(status="VALIDATED")
    valid, error, message = challenge_runner.validate_single_submission(
        SUBMISSION, status, invalid_func, "path")
    assert not valid
    assert isinstance(error, ValueError)
    assert message == ERROR_MESSAGE


def test_storeinvalid_validate_single_submission(challenge_runner):
    '''
    Test storing of status
    '''
    status = synapseclient.SubmissionStatus(status="VALIDATED")
    with patch.object(SYN, "store") as patch_store:
        status = synapseclient.SubmissionStatus(status="VALIDATED")
        valid, error, message = challenge_runner.validate_single_submission(
            SUBMISSION, status, invalid_func, "path")
        expected_status = {
            "annotations": {
                'stringAnnos': [{
                    "isPrivate": False,
                    "key": "FAILURE_REASON",
                    "value": ERROR_MESSAGE
                }]
            },
            "status": "INVALID"
        }
        assert not valid
        assert isinstance(error, ValueError)
        assert message == ERROR_MESSAGE
        patch_store.assert_called_once_with(expected_status)


def test_validate(challenge_runner):
    '''
    Test validate process
    - get evaluation
    - get bundles
    - get submission
    - score single submission
    - get users
    - send emails
    '''
    status = synapseclient.SubmissionStatus(status="SCORED")

    with patch.object(SYN, "getEvaluation",
                      return_value=EVALUATION) as patch_getevaluation,\
         patch.object(SYN, "getSubmissionBundles",
                      return_value=[(SUBMISSION, status)]) as patch_get_bundles,\
         patch.object(SYN, "getSubmission",
                      return_value=SUBMISSION) as patch_get_sub,\
         patch.object(Challenge, "validate_single_submission",
                      return_value=(status,
                                    ValueError("foo"),
                                    "message")) as patch_validate_single,\
         patch.object(SYN, "getUserProfile",
                      return_value=SYN_USERPROFILE) as patch_get_user,\
         patch.object(messages, "validation_passed") as patch_send,\
         patch.object(scoring_harness.challenge, "get_user_name",
                      return_value="foo") as patch_get_user_name:
        challenge_runner.validate(QUEUE_INFO_DICT, [1],
                                  "syn1234", status='RECEIVED')
        patch_getevaluation.assert_called_once_with(QUEUE_INFO_DICT['id'])
        patch_get_bundles.assert_called_once_with(
            EVALUATION,
            status='RECEIVED')
        patch_get_sub.assert_called_once_with(SUBMISSION)
        patch_validate_single.assert_called_once_with(
            SUBMISSION, status,
            validation_func, QUEUE_INFO_DICT['goldstandard_path'])
        patch_get_user.assert_called_once_with(SUBMISSION.userId)
        patch_send.assert_called_once_with(syn=SYN,
                                           userids=[SUBMISSION.userId],
                                           acknowledge_receipt=False,
                                           dry_run=False,
                                           username="foo",
                                           queue_name=EVALUATION.name,
                                           submission_name=SUBMISSION.name,
                                           submission_id=SUBMISSION.id,
                                           challenge_synid="syn1234")
        patch_get_user_name.assert_called_once_with(SYN_USERPROFILE)
