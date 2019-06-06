import sys
import mock
import os
import synapseclient

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(SCRIPT_DIR, '../scoring_harness'))
from challenge import score_single_submission

syn = synapseclient.Synapse()
SCORES = {"score": 5}
MESSAGE = "passed"
ERROR_MESSAGE = "error for days"


def scoring_func(path, truth):
    return(SCORES, MESSAGE)


def invalid_scoring_func(path, truth):
    raise ValueError(ERROR_MESSAGE)


def test_score_single_submission():
    '''
    Test scoring of single submission
    '''
    submission = synapseclient.Submission(
        name="foo", entityId="syn123", evaluationId=2, versionNumber=1,
        id="syn222", filePath="foo", userId="222")
    status = synapseclient.SubmissionStatus(status="VALIDATED")
    status, message = score_single_submission(
        syn, submission, status, scoring_func, "path", dry_run=True)
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
    submission = synapseclient.Submission(
        name="foo", entityId="syn123", evaluationId=2, versionNumber=1,
        id="syn222", filePath="foo", userId="222")
    status = synapseclient.SubmissionStatus(status="VALIDATED")
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
    with mock.patch.object(
            syn, "store",
            return_value=store_return) as patch_store:
        status, message = score_single_submission(
            syn, submission, status, scoring_func, "path")
        patch_store.assert_called_once_with(expected_status)
        # Return the stored status
        assert status == store_return
        assert message == "passed"


def test_invalid_single_submission():
    '''
    Test invalid submission
    '''
    submission = synapseclient.Submission(
        name="foo", entityId="syn123", evaluationId=2, versionNumber=1,
        id="syn222", filePath="foo", userId="222")
    status = synapseclient.SubmissionStatus(status="VALIDATED")
    status, message = score_single_submission(
        syn, submission, status, invalid_scoring_func, "path", dry_run=True)
    assert status == {'status': 'INVALID'}
    assert message == ERROR_MESSAGE
