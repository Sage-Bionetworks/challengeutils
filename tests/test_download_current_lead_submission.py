"""Test download current lead submission"""
import mock
from mock import patch
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