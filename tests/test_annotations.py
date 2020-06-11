"""Test annotations"""
import json
import tempfile
from unittest import mock
from unittest.mock import patch

import synapseclient
from synapseclient import SubmissionStatus

from challengeutils import annotations

syn = mock.create_autospec(synapseclient.Synapse)


def test_annotate_submission_with_json():
    """Test annotation"""
    add_annotations = {'test': 2, 'test2': 2}
    tempfile_path = tempfile.NamedTemporaryFile()
    with open(tempfile_path.name, "w") as annotation_file:
        json.dump(add_annotations, annotation_file)
    status = SubmissionStatus(id="5", etag="12")
    # must use annotations.update_single_submission_status instead of
    # utils because it was imported into annotations.py
    with patch.object(syn, "getSubmissionStatus",
                      return_value=status) as patch_get_submission, \
         patch.object(annotations, "update_single_submission_status",
                      return_value=status) as patch_update, \
         patch.object(annotations, "update_submission_status",
                      return_value=status) as patch_new_update, \
         patch.object(syn, "store") as patch_syn_store:
        response = annotations.annotate_submission_with_json(
            syn, "1234", tempfile_path.name,
            status='SCORED',
            is_private=True,
            force=False
        )
        patch_get_submission.assert_called_once_with("1234")
        patch_update.assert_called_once_with(
            status, add_annotations,
            is_private=True,
            force=False
        )
        patch_new_update.assert_called_once_with(
            status, add_annotations,
            status='SCORED'
        )
        patch_syn_store.assert_called_once_with(status)
        assert response.status_code == 200
