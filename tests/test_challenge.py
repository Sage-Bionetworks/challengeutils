'''
Test scoring harness functions
'''
# pylint: disable=redefined-outer-name
import mock
from mock import patch
import pytest
import synapseclient
import challengeutils.utils
import scoring_harness.challenge
from scoring_harness.challenge import Challenge
from scoring_harness import messages
from scoring_harness.challenge import validate_single_submission
# from scoring_harness.challenge import score_single_submission
# from scoring_harness.challenge import score
# from scoring_harness.challenge import validate

SYN = mock.create_autospec(synapseclient.Synapse)
SCORES = {"score": 5}
VALIDATION_ANNOTATIONS = {'foo': 'bar'}
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
    validation_status = {'valid': True,
                         'annotations': VALIDATION_ANNOTATIONS,
                         'message': MESSAGE}
    return validation_status


def scoring_func(path, truth):
    """Test scoring function"""
    score_status = {'valid': True,
                    'annotations': SCORES,
                    'message': MESSAGE}
    return score_status


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
SUBMISSION_STATUS = synapseclient.SubmissionStatus(status="RECEIVED")
EVALUATION = synapseclient.Evaluation(
    name="foo", id="222", contentSource="syn12")
SYN_USERPROFILE = synapseclient.UserProfile(ownerId="111", userName="foo")
CHALLENGE_SYNID = "syn1234"

def test_score_single_submission(challenge_runner):
    """Test scoring of single submission"""
    challenge_runner.dry_run = True
    status = synapseclient.SubmissionStatus(status="VALIDATED")
    new_status, message = challenge_runner.score_single_submission(
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
    assert new_status == expected_status
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
        mew_status, message = challenge_runner.score_single_submission(
            SUBMISSION, status, scoring_func, "path")
        patch_store.assert_called_once_with(expected_status)
        # Return the stored status
        assert mew_status == store_return
        assert message == MESSAGE


def test_invalid_score_single_submission(challenge_runner):
    '''
    Test invalid submission
    '''
    challenge_runner.dry_run = True
    status = synapseclient.SubmissionStatus(status="VALIDATED")
    new_status, message = challenge_runner.score_single_submission(
        SUBMISSION, status,
        invalid_func, "path")
    assert new_status == {'status': 'INVALID'}
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
         patch.object(messages, "scoring_succeeded") as patch_send:
        challenge_runner.score(QUEUE_INFO_DICT,
                               [1],
                               CHALLENGE_SYNID,
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
                                           username=SYN_USERPROFILE.userName,
                                           queue_name=EVALUATION.name,
                                           submission_name=SUBMISSION.name,
                                           submission_id=SUBMISSION.id,
                                           challenge_synid=CHALLENGE_SYNID)


def test_valid_validate_single_submission():
    '''
    Test validation of single valid submission
    '''
    validation_status = validate_single_submission(SUBMISSION,
                                                   validation_func,
                                                   "path")
    expected_validation_status = {'valid': True,
                                  'annotations': VALIDATION_ANNOTATIONS,
                                  'error': None,
                                  'message': MESSAGE}
    assert expected_validation_status == validation_status


def test_invalid_validate_single_submission():
    '''
    Test invalid submission
    '''

    validation_status = validate_single_submission(SUBMISSION,
                                                   invalid_func,
                                                   "path")
    assert not validation_status['valid']
    assert isinstance(validation_status['error'], ValueError)
    assert validation_status['message'] == ERROR_MESSAGE
    assert validation_status['annotations'] == {}


def test_valid__store_submission_validation_status(challenge_runner):
    """Test storing of submission validation status"""
    expected_validation_status = {'valid': True,
                                  'annotations': VALIDATION_ANNOTATIONS,
                                  'error': None,
                                  'message': MESSAGE}
    expected_status = synapseclient.SubmissionStatus(status="VALIDATED")
    # This is just to make sure that update_single_submission_status
    # has uses the annotations returned by to_submission_status...
    fake_return_annots = 'add'
    with patch.object(SYN, "store") as patch_store,\
         patch.object(scoring_harness.challenge,
                      "to_submission_status_annotations",
                      return_value=fake_return_annots) as patch_toannot,\
         patch.object(scoring_harness.challenge,
                      "update_single_submission_status",
                      return_value=expected_status) as patch_update:
        challenge_runner._store_submission_validation_status(
            SUBMISSION_STATUS, expected_validation_status)
        patch_toannot.assert_called_once_with({"FAILURE_REASON": '', 'foo': 'bar'},
                                              is_private=False)
        patch_update.assert_called_once_with(SUBMISSION_STATUS,
                                             fake_return_annots)
        patch_store.assert_called_once_with(expected_status)


def test_invalid__store_submission_validation_status(challenge_runner):
    """Test error message cutoff at 1000"""
    message = ERROR_MESSAGE*1000
    expected_validation_status = {'valid': False,
                                  'annotations': VALIDATION_ANNOTATIONS,
                                  'error': ValueError,
                                  'message': message}
    expected_status = synapseclient.SubmissionStatus(status="VALIDATED")
    # This is just to make sure that update_single_submission_status
    # has uses the annotations returned by to_submission_status...
    fake_return_annots = 'add'
    with patch.object(SYN, "store") as patch_store,\
         patch.object(scoring_harness.challenge,
                      "to_submission_status_annotations",
                      return_value=fake_return_annots) as patch_toannot,\
         patch.object(scoring_harness.challenge,
                      "update_single_submission_status",
                      return_value=expected_status) as patch_update:
        challenge_runner._store_submission_validation_status(
            SUBMISSION_STATUS, expected_validation_status)
        annot = {"FAILURE_REASON": message[:1000], 'foo': 'bar'}
        patch_toannot.assert_called_once_with(annot, is_private=False)
        patch_update.assert_called_once_with(SUBMISSION_STATUS,
                                             fake_return_annots)
        patch_store.assert_called_once_with(expected_status)


def test_valid__send_validation_email(challenge_runner):
    """Test sending validation success email"""
    expected_validation_status = {'valid': True,
                                  'annotations': VALIDATION_ANNOTATIONS,
                                  'error': None,
                                  'message': MESSAGE}
    with patch.object(messages, "validation_passed") as patch_send,\
         patch.object(SYN, "getUserProfile",
                      return_value=SYN_USERPROFILE) as patch_get_user:
        challenge_runner._send_validation_email(expected_validation_status,
                                                [1],
                                                EVALUATION.name,
                                                SUBMISSION,
                                                CHALLENGE_SYNID)
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
        patch_get_user.assert_called_once_with(SUBMISSION.userId)


def test_error__send_validation_email(challenge_runner):
    """Test sending validation function error email"""
    expected_validation_status = {'valid': False,
                                  'annotations': VALIDATION_ANNOTATIONS,
                                  'error': ValueError(),
                                  'message': ERROR_MESSAGE}
    with patch.object(messages, "validation_failed") as patch_send,\
         patch.object(SYN, "getUserProfile",
                      return_value=SYN_USERPROFILE) as patch_get_user:
        challenge_runner._send_validation_email(expected_validation_status,
                                                [1],
                                                EVALUATION.name,
                                                SUBMISSION,
                                                CHALLENGE_SYNID)
        patch_get_user.assert_called_once_with(SUBMISSION.userId)
        patch_send.assert_called_once_with(syn=SYN,
                                           userids=[1],
                                           send_messages=False,
                                           dry_run=False,
                                           username="Challenge Administrator",
                                           queue_name=EVALUATION.name,
                                           submission_name=SUBMISSION.name,
                                           submission_id=SUBMISSION.id,
                                           message=ERROR_MESSAGE,
                                           challenge_synid=CHALLENGE_SYNID)
        patch_get_user.assert_called_once_with(SUBMISSION.userId)


def test_invalid__send_validation_email(challenge_runner):
    """Test invalid submission email"""
    expected_validation_status = {'valid': False,
                                  'annotations': VALIDATION_ANNOTATIONS,
                                  'error': AssertionError(),
                                  'message': ERROR_MESSAGE}
    with patch.object(messages, "validation_failed") as patch_send,\
         patch.object(SYN, "getUserProfile",
                      return_value=SYN_USERPROFILE) as patch_get_user:
        challenge_runner._send_validation_email(expected_validation_status,
                                                [1],
                                                EVALUATION.name,
                                                SUBMISSION,
                                                CHALLENGE_SYNID)
        patch_get_user.assert_called_once_with(SUBMISSION.userId)
        patch_send.assert_called_once_with(syn=SYN,
                                           userids=[SUBMISSION.userId],
                                           send_messages=False,
                                           dry_run=False,
                                           username=SYN_USERPROFILE.userName,
                                           queue_name=EVALUATION.name,
                                           submission_name=SUBMISSION.name,
                                           submission_id=SUBMISSION.id,
                                           message=ERROR_MESSAGE,
                                           challenge_synid=CHALLENGE_SYNID)
        patch_get_user.assert_called_once_with(SUBMISSION.userId)


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
    validation_info = {'valid': True,
                       'annotations': VALIDATION_ANNOTATIONS,
                       'error': None,
                       'message': MESSAGE}
    with patch.object(SYN, "getEvaluation",
                      return_value=EVALUATION) as patch_getevaluation,\
         patch.object(SYN, "getSubmissionBundles",
                      return_value=[(SUBMISSION, status)]) as patch_get_bundles,\
         patch.object(SYN, "getSubmission",
                      return_value=SUBMISSION) as patch_get_sub,\
         patch.object(scoring_harness.challenge,
                      "validate_single_submission",
                      return_value=validation_info) as patch_validate_single,\
         patch.object(challenge_runner,
                      "_store_submission_validation_status") as patch_store,\
         patch.object(challenge_runner,
                      "_send_validation_email") as patch_send:
        challenge_runner.validate(QUEUE_INFO_DICT, [1],
                                  CHALLENGE_SYNID, status='RECEIVED')
        patch_getevaluation.assert_called_once_with(QUEUE_INFO_DICT['id'])
        patch_get_bundles.assert_called_once_with(
            EVALUATION,
            status='RECEIVED')
        patch_get_sub.assert_called_once_with(SUBMISSION)
        patch_validate_single.assert_called_once_with(
            SUBMISSION, validation_func, QUEUE_INFO_DICT['goldstandard_path'])
        patch_store.assert_called_once_with(status, validation_info)
        patch_send.assert_called_once_with(validation_info, [1],
                                           EVALUATION.name, SUBMISSION,
                                           CHALLENGE_SYNID)