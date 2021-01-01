'''
Test challengeutils.utils functions
'''
import json
import re
import tempfile
from unittest import mock
from unittest.mock import Mock, patch
import uuid

import pytest
import synapseclient
from synapseclient.annotations import to_submission_status_annotations
from synapseclient.core.exceptions import SynapseHTTPError

import challengeutils.utils

syn = mock.create_autospec(synapseclient.Synapse)


def test_raiseerror__switch_annotation_permission():
    '''
    Test that annotations permission isn't switched
    '''
    add_annotations = {'test': 2, 'test2': 2}
    existing_annotations = {'test': 1}
    error_message = (
        "You are trying to change the ACL of these annotation key(s): "
        "test. Either change the annotation key or specify "
        "force=True")
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
        force=True)
    assert existing == {}


def test_nooverlap__switch_annotation_permission():
    '''
    Test no overlap of annotations to add and existing annotations
    '''
    add_annotations = {'test': 2, 'test2': 2}
    existing_annotations = {'test3': 1}
    existing = challengeutils.utils._switch_annotation_permission(
        add_annotations, existing_annotations,
        force=True)
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
        status, add_annotations, is_private=False)
    expected_annot = to_submission_status_annotations(
        add_annotations, is_private=False)
    expected_status = {'annotations': expected_annot}
    assert new_status == expected_status


def test_valid__check_date_range():
    '''
    Test checking valid date range
    '''
    date_str = '2019-05-26T23:59:59.062Z'
    datetime1 = '2019-05-06 1:00'
    datetime2 = '2019-06-01 1:00'
    result = challengeutils.utils._check_date_range(date_str,
                                                    datetime1,
                                                    datetime2)
    assert result


def test_invalid__check_date_range():
    '''
    Test checking invalid date range
    '''
    date_str = '2019-05-26T23:59:59.062Z'
    datetime1 = '2019-05-06 1:00'
    datetime2 = '2019-06-01 1:00'
    result = challengeutils.utils._check_date_range(date_str,
                                                    datetime2,
                                                    None)
    assert not result


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
            syn, 123, "SCORED","2019-05-06 1:00","2019-06-01 1:00")
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
            syn, ids, "SCORED")
        assert all_contributors == set([321])


def test_list_evaluations():
    with mock.patch.object(
            syn, "getEvaluationByContentSource") as patch_geteval:
        challengeutils.utils.list_evaluations(syn, "syn1234")
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
        sub_dict = challengeutils.utils.download_submission(syn, "12345")
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
            syn, "12345", download_location=".")
        patch_get_submission.assert_called_once_with(
            "12345", downloadLocation=".")
        assert sub_dict == expected_submission_dict


def test_userid__get_submitter_name():
    """Get username if userid is passed in"""
    submitterid = 2222
    userinfo = {"userName": "foo"}
    with mock.patch.object(syn, "getUserProfile",
                           return_value=userinfo) as patch_get_user,\
         mock.patch.object(syn, "getTeam") as patch_get_team:
        submittername = challengeutils.utils._get_submitter_name(syn,
                                                                 submitterid)
        assert submittername == userinfo['userName']
        patch_get_user.assert_called_once_with(submitterid)
        patch_get_team.assert_not_called()


def test_teamid__get_submitter_name():
    """Get teamname if teamid is passed in"""
    submitterid = 2222
    teaminfo = {"name": "foo"}
    with mock.patch.object(syn, "getUserProfile",
                           side_effect=SynapseHTTPError) as patch_get_user,\
         mock.patch.object(syn, "getTeam",
                           return_value=teaminfo) as patch_get_team:
        submittername = challengeutils.utils._get_submitter_name(syn,
                                                                 submitterid)
        assert submittername == teaminfo['name']
        patch_get_user.assert_called_once_with(submitterid)
        patch_get_team.assert_called_once_with(submitterid)


def test_delete_submission():
    """Test deleting a submission"""
    sub = Mock()
    with patch.object(syn, "getSubmission", return_value=sub) as patch_get,\
         patch.object(syn, "delete") as patch_delete:
        challengeutils.utils.delete_submission(syn, "12345")
        patch_get.assert_called_once_with("12345", downloadFile=False)
        patch_delete.assert_called_once_with(sub)
