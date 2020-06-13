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


def test__convert_to_annotation_cls_dict():
    """Test that dictionary is converted to synapseclient.Annotations"""
    status = SubmissionStatus(id="5", etag="12")

    annotation_cls = annotations._convert_to_annotation_cls(
        status,
        {"foo": "test"}
    )
    assert isinstance(annotation_cls, annotations.Annotations)
    assert annotation_cls == {"foo": "test"}
    assert annotation_cls.id == '5'
    assert annotation_cls.etag == '12'


def test__convert_to_annotation_cls_synapse_style():
    """Test that synapse style annotations is converted to
    synapseclient.Annotations"""
    status = SubmissionStatus(id="5", etag="12")
    annots = {
        'id': '6',
        'etag': '123',
        'annotations': {
            'foo': {
                'type': 'STRING',
                'value': ['doo']
            }
        }
    }
    annotation_cls = annotations._convert_to_annotation_cls(
        status, annots
    )
    assert isinstance(annotation_cls, annotations.Annotations)
    assert annotation_cls == {"foo": ["doo"]}
    assert annotation_cls.id == '6'
    assert annotation_cls.etag == '123'


def test_update_submission_status_empty():
    """Test update empty existing submission annotations"""
    sub_status = SubmissionStatus(id="5", etag="12")
    expected_status = {
        'id': '5',
        'etag': '12',
        "submissionAnnotations": {
            'annotations': {
                'foo': {
                    'type': 'STRING',
                    'value': ['doo']
                }
            },
            'id': '5',
            'etag': '12'
        },
        'status': "RECEIVED"
    }
    new_status = annotations.update_submission_status(
        sub_status, {"foo": "doo"}, status="RECEIVED"
    )
    assert new_status == expected_status


def test_update_submission_status():
    """Test update existing submission annotations"""
    sub_status = SubmissionStatus(id="5", etag="12",
                                  submissionAnnotations={"foo": "test"})
    expected_status = {
        'id': '5',
        'etag': '12',
        "submissionAnnotations": {
            'annotations': {
                'foo': {
                    'type': 'STRING',
                    'value': ['doo']
                },
                'new': {
                    'type': 'STRING',
                    'value': ['wow']
                }
            },
            'id': '5',
            'etag': '12'
        }
    }
    new_status = annotations.update_submission_status(
        sub_status, {"foo": "doo", "new": "wow"}
    )
    assert new_status == expected_status