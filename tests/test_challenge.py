import mock
import synapseclient
from scoring_harness.challenge import score_single_submission
from scoring_harness.challenge import score

syn = synapseclient.Synapse()
SCORES = {"score": 5}
MESSAGE = "passed"
ERROR_MESSAGE = "error for days"


def scoring_func(path, truth):
    return(SCORES, MESSAGE)


def invalid_scoring_func(path, truth):
    raise ValueError(ERROR_MESSAGE)


QUEUE_INFO_DICT = {
    'id': '1', 'scoring_func': scoring_func, 'goldstandard_path': "./"}
SUBMISSION = synapseclient.Submission(
    name="foo", entityId="syn123", evaluationId=2, versionNumber=1,
    id="syn222", filePath="foo", userId="222")
EVALUATION = synapseclient.Evaluation(
    name="foo", id="222", contentSource="syn12")
SYN_USERPROFILE = synapseclient.UserProfile(ownerId="111")


def test_score_single_submission():
    '''
    Test scoring of single submission
    '''
    status = synapseclient.SubmissionStatus(status="VALIDATED")
    status, message = score_single_submission(
        syn, SUBMISSION, status, scoring_func, "path", dry_run=True)
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


def test_storestatus_score_single_submission():
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
    with mock.patch.object(
            syn, "store",
            return_value=store_return) as patch_store:
        status, message = score_single_submission(
            syn, SUBMISSION, status, scoring_func, "path")
        patch_store.assert_called_once_with(expected_status)
        # Return the stored status
        assert status == store_return
        assert message == "passed"


def test_invalid_single_submission():
    '''
    Test invalid submission
    '''
    status = synapseclient.SubmissionStatus(status="VALIDATED")
    status, message = score_single_submission(
        syn, SUBMISSION, status,
        invalid_scoring_func, "path", dry_run=True)
    assert status == {'status': 'INVALID'}
    assert message == ERROR_MESSAGE


def test_score():
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

    with mock.patch.object(
        syn, "getEvaluation", return_value=EVALUATION) as patch_getevaluation,\
            mock.patch.object(
                syn, "getSubmissionBundles",
                return_value=[(SUBMISSION, status)]) as patch_get_bundles,\
            mock.patch.object(
                syn, "getSubmission",
                return_value=SUBMISSION) as patch_get_sub,\
            mock.patch(
                "scoring_harness.challenge.score_single_submission",
                return_value=(status, "message")) as patch_score_single,\
            mock.patch.object(
                syn, "getUserProfile",
                return_value=SYN_USERPROFILE) as patch_get_user,\
            mock.patch(
                "scoring_harness.messages.scoring_succeeded") as patch_send,\
            mock.patch(
                "scoring_harness.challenge.get_user_name",
                return_value="foo") as patch_get_user_name:
        score(syn,
              QUEUE_INFO_DICT,
              [1],
              "syn1234",
              status='VALIDATED',
              send_messages=False,
              send_notifications=False,
              dry_run=False)
        patch_getevaluation.assert_called_once_with(QUEUE_INFO_DICT['id'])
        patch_get_bundles.assert_called_once_with(
            EVALUATION, status='VALIDATED')
        patch_get_sub.assert_called_once_with(SUBMISSION)
        patch_score_single.assert_called_once_with(
            syn, SUBMISSION, status,
            scoring_func, QUEUE_INFO_DICT['goldstandard_path'],
            dry_run=False)
        patch_get_user.assert_called_once_with(SUBMISSION.userId)
        patch_send.assert_called_once_with(
            syn=syn,
            userIds=[SUBMISSION.userId],
            send_messages=False,
            dry_run=False,
            message="message",
            username="foo",
            queue_name=EVALUATION.name,
            submission_name=SUBMISSION.name,
            submission_id=SUBMISSION.id,
            challenge_synid="syn1234"
        )
        patch_get_user_name.assert_called_once_with(SYN_USERPROFILE)
