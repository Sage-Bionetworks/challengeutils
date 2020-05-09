"""Test download current lead submission"""
import os
import tempfile
from unittest import mock
from unittest.mock import patch

import pytest
import synapseclient

from challengeutils import utils
import challengeutils.download_current_lead_submission as dl_cur

SYN = mock.create_autospec(synapseclient.Synapse)
SUBMISSIONID = "111"
QUEUEID = "333"


def test_nosub_get_submitterid_from_submission_id():
    """Tests if submission id doesn't exist"""
    with pytest.raises(ValueError,
                       match=r'submission id*'),\
        patch.object(utils, "evaluation_queue_query",
                     return_value=[]) as patch_query:
        dl_cur.get_submitterid_from_submission_id(SYN, SUBMISSIONID, QUEUEID,
                                                  verbose=False)
        patch_query.assert_called_once()


def test_get_submitterid_from_submission_id():
    """Tests getting of submitter id"""
    with patch.object(utils, "evaluation_queue_query",
                      return_value=[{'submitterId': 1}]) as patch_query:
        submitter = dl_cur.get_submitterid_from_submission_id(SYN,
                                                              SUBMISSIONID,
                                                              QUEUEID,
                                                              verbose=False)
        patch_query.assert_called_once()
        assert submitter == 1


def test_get_submitters_lead_submission():
    """Tests getting of lead submission"""
    submission = synapseclient.Submission(evaluationId='2', entityId='2',
                                          versionNumber='3')
    temp = tempfile.NamedTemporaryFile()
    submission.filePath = temp.name

    with patch.object(utils, "evaluation_queue_query",
                      return_value=[{'objectId': 1}]) as patch_query,\
        patch.object(SYN, "getSubmission",
                     return_value=submission) as patch_getsub:
        dl_file = dl_cur.get_submitters_lead_submission(SYN,
                                                        SUBMISSIONID,
                                                        QUEUEID,
                                                        "key",
                                                        verbose=False)
        patch_query.assert_called_once()
        patch_getsub.assert_called_once_with(1, downloadLocation='.')
        assert dl_file == "previous_submission.csv"
        os.unlink("previous_submission.csv")


def test_none_get_submitters_lead_submission():
    """Tests not getting submission"""
    with patch.object(utils, "evaluation_queue_query",
                      return_value=[]) as patch_query:
        dl_file = dl_cur.get_submitters_lead_submission(SYN,
                                                        SUBMISSIONID,
                                                        QUEUEID,
                                                        "key",
                                                        verbose=False)
        patch_query.assert_called_once()
        assert dl_file is None


def test_download_current_lead_sub():
    """Tests download of lead submission"""
    submission = synapseclient.Submission(evaluationId='2', entityId='2',
                                          versionNumber='3')
    with patch.object(SYN, "getSubmission",
                      return_value=submission) as patch_getsub,\
        patch.object(dl_cur, "get_submitterid_from_submission_id",
                     return_value="2") as patch_getsubmitter,\
        patch.object(dl_cur, "get_submitters_lead_submission",
                     return_value="path") as patch_get_lead:
        dl_file = dl_cur.download_current_lead_sub(SYN, SUBMISSIONID,
                                                   "VALIDATED",
                                                   "key",
                                                   verbose=False)
        patch_getsubmitter.assert_called_once()
        patch_get_lead.assert_called_once()
        assert dl_file == "path"


def test_invalid_download_current_lead_sub():
    """Tests None is downloaded if status is INVALID"""
    dl_file = dl_cur.download_current_lead_sub(SYN, SUBMISSIONID,
                                               "INVALID", "key",
                                               verbose=False)
    assert dl_file is None