import json
import mock
from mock import patch
import os
import pytest
import re
import challengeutils.utils
import synapseclient
from synapseclient.annotations import to_submission_status_annotations
from challengeutils.synapse import Synapse
syn = mock.create_autospec(synapseclient.Synapse)
Synapse._synapse_client = syn

def test_raiseerror__switch_annotation_permission():
    '''
    Test that annotations permission isn't switched
    '''
    add_annotations = {'test': 2, 'test2': 2}
    existing_annotations = {'test': 1}
    error_message = (
        "You are trying to change the ACL of these annotation key(s): "
        "test. Either change the annotation key or specify "
        "force_change_annotation_acl=True")
    # Must use re.escape() because match accepts regex
    with pytest.raises(ValueError, match=re.escape(error_message)):
        challengeutils.utils._switch_annotation_permission(
            add_annotations, existing_annotations)


def test_filter__switch_annotation_permission():
    '''
    Test filtering out of switched annotations
    '''
    add_annotations = {'test': 2, 'test2': 2}
    existing_annotations = {'test': 1}
    existing = challengeutils.utils._switch_annotation_permission(
        add_annotations, existing_annotations,
        force_change_annotation_acl=True)
    assert existing == {}


def test_nooverlap__switch_annotation_permission():
    '''
    Test no overlap of annotations to add and existing annotations
    '''
    add_annotations = {'test': 2, 'test2': 2}
    existing_annotations = {'test3': 1}
    existing = challengeutils.utils._switch_annotation_permission(
        add_annotations, existing_annotations,
        force_change_annotation_acl=True)
    assert existing == existing_annotations


def test_append_update_single_submission_status():
    '''
    Test appending new annotation (dict)
    '''
    existing = {"test": "foo", "test1": "d", "test2": 5, "test3": 2.2}
    existing = to_submission_status_annotations(existing)
    status = {'annotations': existing}
    add_annotations = {"test4": 5}
    new_status = challengeutils.utils.update_single_submission_status(
        status, add_annotations)

    status['annotations']['longAnnos'].append(
         {'key': 'test4', 'value': 5, 'isPrivate': True}
    )
    assert new_status == status


def test_update_update_single_submission_status():
    '''
    Test updating new annotation to change type (dict)
    '''
    existing = {"test": "foo"}
    existing = to_submission_status_annotations(existing)
    status = {'annotations': existing}
    add_annotations = {"test": 5}
    new_status = challengeutils.utils.update_single_submission_status(
        status, add_annotations)
    new_annots = synapseclient.annotations.to_submission_status_annotations(
        add_annotations)
    expected_status = {'annotations': new_annots}
    assert new_status == expected_status


def test_substatus_update_single_submission_status():
    '''
    Test passing in submission annotation format
    '''
    existing = {"test": 5}
    existing = to_submission_status_annotations(existing)
    status = {'annotations': existing}
    add_annotations = to_submission_status_annotations({"test": 2.4})
    expected_status = {'annotations': add_annotations}
    new_status = challengeutils.utils.update_single_submission_status(
        status, add_annotations)
    assert new_status == expected_status


def test_topublic_update_single_submission_status():
    '''
    Test topublic flag. By default when a dict is passed in
    the annotation is set to private, but you can change that flag
    '''
    status = {'annotations': {}}
    add_annotations = {"test": 2.4}
    new_status = challengeutils.utils.update_single_submission_status(
        status, add_annotations, to_public=True)
    expected_annot = to_submission_status_annotations(
        add_annotations, is_private=False)
    expected_status = {'annotations': expected_annot}
    assert new_status == expected_status

def test__check_date_range():
    '''
    Test checking date range
    '''
    date_str = '2019-05-26T23:59:59.062Z'
    datetime1 = '2019-05-06 1:00'
    datetime2 = '2019-06-01 1:00'
    result = [challengeutils.utils._check_date_range(date_str, datetime1, datetime2),
              challengeutils.utils._check_date_range(date_str, datetime2, None)]
    expected_result = [True,False]
    assert result == expected_result


def test__get_contributors():
    '''
    Test getting contributors by evaluationID, status, and date range
    '''
    sub = synapseclient.Submission(evaluationId=123, entityId="syn1234", versionNumber=1,
                                   contributors=[{"principalId": 321}], createdOn="2019-05-26T23:59:59.062Z")
    bundle = [(sub, "temp")]
    with patch.object(syn, "getSubmissionBundles",
                      return_value=bundle) as patch_syn_get_bundles:
        contributors = challengeutils.utils._get_contributors(
            123, "SCORED","2019-05-06 1:00","2019-06-01 1:00")
        patch_syn_get_bundles.assert_called_once_with(
            123,
            status="SCORED")
        assert contributors == set([321])

def test_get_contributors():
    '''
    Test getting contributors by a list of evaluation IDs
    '''
    contributors = set([321])
    ids = [123]
    with patch.object(challengeutils.utils, "_get_contributors",
                      return_value=contributors) as patch_syn_get_bundles:
        all_contributors = challengeutils.utils.get_contributors(
            ids, "SCORED")
        assert all_contributors == set([321])

def test_list_evaluations():
    with mock.patch.object(
            syn, "getEvaluationByContentSource") as patch_geteval:
        challengeutils.utils.list_evaluations("syn1234")
        patch_geteval.assert_called_once_with("syn1234")


def test_defaultloc_download_submission():
    '''
    Download submission json object with default None location
    '''
    entity = synapseclient.Entity(concreteType='foo', id='syn123')
    submission_dict = {
        'dockerRepositoryName': 'foo',
        'dockerDigest': 'foo',
        'entity': entity,
        'evaluationId': 12345,
        'filePath': '/path/here'}
    expected_submission_dict = {
        'docker_repository': 'foo',
        'docker_digest': 'foo',
        'entity_id': entity['id'],
        'entity_version': entity.get('versionNumber'),
        'entity_type': entity.get('concreteType'),
        'evaluation_id': 12345,
        'file_path': '/path/here'}
    with mock.patch.object(
            syn, "getSubmission",
            return_value=submission_dict) as patch_get_submission:
        sub_dict = challengeutils.utils.download_submission("12345")
        patch_get_submission.assert_called_once_with(
            "12345", downloadLocation=None)
        assert sub_dict == expected_submission_dict


def test_specifyloc_download_submission():
    '''
    Download submission json object with specified location
    '''
    entity = synapseclient.Entity(
        versionNumber=4, concreteType='foo', id='syn123')
    submission_dict = {
        'entity': entity,
        'evaluationId': 12345,
        'filePath': '/path/here'}
    expected_submission_dict = {
        'docker_repository': None,
        'docker_digest': None,
        'entity_id': entity['id'],
        'entity_version': entity.get('versionNumber'),
        'entity_type': entity.get('concreteType'),
        'evaluation_id': 12345,
        'file_path': '/path/here'}
    with mock.patch.object(
            syn, "getSubmission",
            return_value=submission_dict) as patch_get_submission:
        sub_dict = challengeutils.utils.download_submission(
            "12345", download_location=".")
        patch_get_submission.assert_called_once_with(
            "12345", downloadLocation=".")
        assert sub_dict == expected_submission_dict


def test_annotate_submission_with_json():
    add_annotations = {'test': 2, 'test2': 2}
    tempfile_path = "temp.json"
    with open(tempfile_path, "w") as annotation_file:
        json.dump(add_annotations, annotation_file)
    status = {"foo": "bar"}
    with mock.patch.object(
            syn, "getSubmissionStatus",
            return_value=status) as patch_get_submission, \
        mock.patch.object(
            challengeutils.utils, "update_single_submission_status",
            return_value=status) as patch_update, \
            mock.patch.object(syn, "store") as patch_syn_store:
        challengeutils.utils.annotate_submission_with_json(
            "1234", tempfile_path,
            to_public=False,
            force_change_annotation_acl=False)
        patch_get_submission.assert_called_once_with("1234")
        patch_update.assert_called_once_with(
            status, add_annotations,
            to_public=False,
            force_change_annotation_acl=False)
        patch_syn_store.assert_called_once_with(status)
    os.unlink(tempfile_path)

