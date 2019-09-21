"""Testing writeup attacher"""
import time
import mock
from mock import patch
import pandas as pd
import synapseclient
from synapseclient.annotations import to_submission_status_annotations
import synapseutils

import challengeutils.utils
import challengeutils.project_submission
from challengeutils.project_submission import create_copy_project
from challengeutils.project_submission import _archive_project_submission
from challengeutils.project_submission import archive_project_submission
from challengeutils.project_submission import archive_project_submissions
#from challengeutils.project_submission import attach_writeup_to_main_submission
#from challengeutils.project_submission import archive_and_attach_writeups


SYN = mock.create_autospec(synapseclient.Synapse)
ENTITY = synapseclient.File(name='test', parentId="syn123", id="syn222")
SUBMISSION = synapseclient.Submission(name="wow", entityId=ENTITY['id'],
                                      evaluationId="123", versionNumber=2,
                                      entity=ENTITY, id=333)

SUB_ANNOTATIONS = to_submission_status_annotations({"test": "1"})
SUB_STATUS = synapseclient.SubmissionStatus(annotations=SUB_ANNOTATIONS)


def test_create_copy_project():
    """Create new Synapse Project then copy content to it"""
    archived_name = "new project"
    project = synapseclient.Project(archived_name)
    return_project = synapseclient.Project(archived_name, id="syn888")
    with patch.object(SYN, "store",
                      return_value=return_project) as patch_syn_store,\
         patch.object(synapseutils, "copy") as patch_syn_copy:
        archived_project = create_copy_project(SYN, SUBMISSION.entityId,
                                               archived_name)
        assert archived_project == return_project
        patch_syn_store.assert_called_once_with(project)
        patch_syn_copy.assert_called_once_with(SYN, SUBMISSION.entityId,
                                               archived_project.id)


def test__archive_project_submission():
    """Create archive project submission"""
    archived_name = (f"Archived {SUBMISSION.entity.name} 10000 "
                     f"{SUBMISSION.id} {SUBMISSION.entityId}")
    # This 'project' is used for the assert call
    project = synapseclient.Project(archived_name)
    # The returned project must have id as the id is used in copy call
    return_project = synapseclient.Project(archived_name, id="syn888")
    # The time value is multipled by 1000
    with patch.object(time, "time", return_value=10), \
         patch.object(challengeutils.project_submission,
                      "create_copy_project",
                      return_value=return_project) as patch_create:
        archive_proj = _archive_project_submission(SYN, SUBMISSION)
        assert archive_proj == return_project
        patch_create.assert_called_once_with(SYN, SUBMISSION.entityId,
                                             archived_name)


def test_alreadyarchived_archive_project():
    """
    If the archive annotation already exists the project submission shouldn't
    be archived, making sure that the archived entity id is returned.
    """
    annotations = {"archived": "1"}
    syn_annots = to_submission_status_annotations(annotations)
    submission_status = synapseclient.SubmissionStatus(annotations=syn_annots)
    with patch.object(SYN, "getSubmission",
                      return_value=SUBMISSION) as patch_getsub,\
         patch.object(SYN, "getSubmissionStatus",
                      return_value=submission_status) as patch_getsubstatus,\
         patch.object(challengeutils.project_submission,
                      "_archive_project_submission") as patch__archive,\
         patch.object(challengeutils.utils,
                      "update_single_submission_status") as patch_update,\
         patch.object(SYN, "store") as patch_syn_store:
        archive_proj = archive_project_submission(SYN, SUBMISSION.id)
        patch_getsub.assert_called_once_with(SUBMISSION.id, downloadFile=False)
        patch_getsubstatus.assert_called_once_with(SUBMISSION.id)
        patch__archive.assert_not_called()
        patch_update.assert_not_called()
        patch_syn_store.assert_not_called()
        # The archive project entity id should be returned
        assert archive_proj == annotations['archived']


def test_notarchive_archive_project_submission():
    """Archive project submission if there is not an archive"""
    return_project = synapseclient.Project("test", id="syn2222")
    annotations = {"archived": "syn2222"}
    syn_annots = to_submission_status_annotations(annotations)
    archive_substatus = synapseclient.SubmissionStatus(annotations=syn_annots)
    with patch.object(SYN, "getSubmission",
                      return_value=SUBMISSION) as patch_getsub,\
         patch.object(SYN, "getSubmissionStatus",
                      return_value=archive_substatus) as patch_getsubstatus,\
         patch.object(challengeutils.project_submission,
                      "_archive_project_submission",
                      return_value=return_project) as patch__archive,\
         patch.object(challengeutils.utils,
                      "update_single_submission_status",
                      return_value=archive_substatus) as patch_update,\
         patch.object(SYN, "store") as patch_syn_store:
        archive_proj = archive_project_submission(SYN, SUBMISSION.id,
                                                  rearchive=True)
        patch_getsub.assert_called_once_with(SUBMISSION.id, downloadFile=False)
        patch_getsubstatus.assert_called_once_with(SUBMISSION.id)
        patch__archive.assert_called_once_with(SYN, SUBMISSION)
        patch_update.assert_called_once_with(archive_substatus,
                                             annotations)
        patch_syn_store.assert_called_once_with(archive_substatus)
        assert archive_proj == return_project.id


def test_forcerearchive_archive_project_submission():
    """
    Archive project submission even if there is already an archive but
    rearchive=True
    """
    submission_status = synapseclient.SubmissionStatus(annotations={})
    return_project = synapseclient.Project("test", id="syn2222")
    annotations = {"archived": "syn2222"}
    syn_annots = to_submission_status_annotations(annotations)
    archive_substatus = synapseclient.SubmissionStatus(annotations=syn_annots)
    with patch.object(SYN, "getSubmission",
                      return_value=SUBMISSION) as patch_getsub,\
         patch.object(SYN, "getSubmissionStatus",
                      return_value=submission_status) as patch_getsubstatus,\
         patch.object(challengeutils.project_submission,
                      "_archive_project_submission",
                      return_value=return_project) as patch__archive,\
         patch.object(challengeutils.utils,
                      "update_single_submission_status",
                      return_value=archive_substatus) as patch_update,\
         patch.object(SYN, "store") as patch_syn_store:
        archive_proj = archive_project_submission(SYN, SUBMISSION.id)
        patch_getsub.assert_called_once_with(SUBMISSION.id, downloadFile=False)
        patch_getsubstatus.assert_called_once_with(SUBMISSION.id)
        patch__archive.assert_called_once_with(SYN, SUBMISSION)
        patch_update.assert_called_once_with(submission_status,
                                             annotations)
        patch_syn_store.assert_called_once_with(archive_substatus)
        assert archive_proj == return_project.id


def test_default_params_archive_project_submissions():
    """Archive project submissions given evaluation queue"""
    eval_obj = synapseclient.Evaluation(id=1234, contentSource="syn123",
                                        name="test")
    query = "select objectId from evaluation_1234 where STATUS == VALIDATED"
    query_results = [{'objectId': SUBMISSION.id}]
    with patch.object(challengeutils.utils, "evaluation_queue_query",
                      return_value=query_results) as patch_query,\
         patch.object(challengeutils.project_submission,
                      "archive_project_submission",
                      return_value="syn1234") as patch_archive:
        archived = archive_project_submissions(SYN, eval_obj.id)
        patch_query.assert_called_once_with(SYN, query)
        patch_archive.assert_called_once_with(SYN, SUBMISSION.id,
                                              rearchive=False)
        assert archived == ['syn1234']


def test_nondefault_params_archive_project_submissions():
    """Archive project submissions given evaluation queue with non default
    params"""
    eval_obj = synapseclient.Evaluation(id=1234, contentSource="syn123",
                                        name="test")
    query = "select objectId from evaluation_1234 where prediction == SCORED"
    query_results = [{'objectId': SUBMISSION.id}]
    with patch.object(challengeutils.utils, "evaluation_queue_query",
                      return_value=query_results) as patch_query,\
         patch.object(challengeutils.project_submission,
                      "archive_project_submission",
                      return_value="syn1234") as patch_archive:
        archived = archive_project_submissions(SYN, eval_obj,
                                               status_key="prediction",
                                               status="SCORED",
                                               rearchive=True)
        patch_query.assert_called_once_with(SYN, query)
        patch_archive.assert_called_once_with(SYN, SUBMISSION.id,
                                              rearchive=True)
        assert archived == ['syn1234']


def test_multiple_submissions_archive_project_submissions():
    """
    Archive project submissions given evaluation queue that has multiple
    submissions
    """
    eval_obj = synapseclient.Evaluation(id=1234, contentSource="syn123",
                                        name="test")
    query_results = [{'objectId': SUBMISSION.id}, {'objectId': SUBMISSION.id}]
    query = "select objectId from evaluation_1234 where STATUS == VALIDATED"

    with patch.object(challengeutils.utils, "evaluation_queue_query",
                      return_value=query_results) as patch_query,\
         patch.object(challengeutils.project_submission,
                      "archive_project_submission",
                      return_value="syn1234") as patch_archive:
        archived = archive_project_submissions(SYN, eval_obj)
        patch_query.assert_called_once_with(SYN, query)
        assert patch_archive.call_count == 2
        assert archived == ['syn1234', 'syn1234']


# def test_nullentity_attach_writeup_to_main_submission():
#     """Nothing should be called if no entityId"""
#     row = {"submitterId": '123',
#            'objectId': '2222',
#            'archived': "syn1234",
#            'entityId': float('nan')}
#     with patch.object(SYN, "getSubmissionStatus") as patch_getsubstatus,\
#          patch.object(challengeutils.project_submission,
#                       "archive_project_submission") as patch_archive,\
#          patch.object(challengeutils.utils,
#                       "update_single_submission_status") as patch_update,\
#          patch.object(SYN, "store") as patch_synstore:
#         attach_writeup_to_main_submission(SYN, row)
#         patch_getsubstatus.assert_not_called()
#         patch_archive.assert_not_called()
#         patch_update.assert_not_called()
#         patch_synstore.assert_not_called()


# def test_alreadyarchived_attach_writeup_to_main_submission():
#     """Specify archived id if writeup has been archived"""
#     row = {"submitterId": '123',
#            'objectId': '2222',
#            'archived': "syn1234",
#            'entityId': "syn2222"}
#     add_writeup_dict = {'writeUp': row['entityId'],
#                         'archivedWriteUp': row['archived']}
#     add_writeup = to_submission_status_annotations(add_writeup_dict,
#                                                    is_private=False)
#     with patch.object(SYN, "getSubmissionStatus",
#                       return_value=SUB_STATUS) as patch_getsubstatus,\
#          patch.object(challengeutils.project_submission,
#                       "archive_project_submission") as patch_archive,\
#          patch.object(challengeutils.utils,
#                       "update_single_submission_status",
#                       return_value=SUB_STATUS) as patch_update,\
#          patch.object(SYN, "store") as patch_synstore:
#         attach_writeup_to_main_submission(SYN, row)
#         patch_getsubstatus.assert_called_once_with(row['objectId'])
#         patch_archive.assert_not_called()
#         patch_update.assert_called_once_with(SUB_STATUS, add_writeup)
#         patch_synstore.assert_called_once_with(SUB_STATUS)



# def test_toarchive_attach_writeup_to_main_submission():
#     """Writeup must be archived if it hasn't already been archived"""
#     row = {"submitterId": '123',
#            'objectId': '2222',
#            'archived': None,
#            'entityId': "syn2222",
#            'writeup_submissionid': '3333'}
#     archived_synid = "syn3333"
#     add_writeup_dict = {'writeUp': row['entityId'],
#                         'archivedWriteUp': archived_synid}
#     add_writeup = to_submission_status_annotations(add_writeup_dict,
#                                                    is_private=False)
#     with patch.object(SYN, "getSubmissionStatus",
#                       return_value=SUB_STATUS) as patch_getsubstatus,\
#          patch.object(challengeutils.project_submission,
#                       "archive_project_submission",
#                       return_value=archived_synid) as patch_archive,\
#          patch.object(challengeutils.utils,
#                       "update_single_submission_status",
#                       return_value=SUB_STATUS) as patch_update,\
#          patch.object(SYN, "store") as patch_synstore:
#         attach_writeup_to_main_submission(SYN, row)
#         patch_getsubstatus.assert_called_once_with(row['objectId'])
#         patch_archive.assert_called_once_with(SYN,
#                                               row['writeup_submissionid'])
#         patch_update.assert_called_once_with(SUB_STATUS, add_writeup)
#         patch_synstore.assert_called_once_with(SUB_STATUS)


# def test_archive_and_attach_writeups():
#     """Archive and attach writeups"""
#     writeups = [{"submitterId": '123',
#                  'objectId': '2222',
#                  'archived': None,
#                  'entityId': "syn2222"}]

#     submissions = [{"submitterId": '123',
#                     'objectId': '3333'}]

#     firstquery = ("select objectId, submitterId, entityId, archived "
#                   "from evaluation_2 where STATUS == 'VALIDATED'")

#     secondquery = ("select objectId, submitterId from "
#                    "evaluation_3 where STATUS == 'SCORED'")
#     with patch.object(challengeutils.utils,
#                       "evaluation_queue_query",
#                       side_effect=[writeups,
#                                    submissions]) as patch_query,\
#          patch.object(challengeutils.project_submission,
#                       "attach_writeup_to_main_submission") as patch_attach:
#         archive_and_attach_writeups(SYN, '2', '3')
#         assert patch_query.call_count == 2
#         calls = [mock.call(SYN, firstquery), mock.call(SYN, secondquery)]
#         patch_query.assert_has_calls(calls)
#         patch_attach.assert_called_once()


# def test_statuskey_archive_and_attach_writeups():
#     """Archive and attach writeups"""
#     writeups = [{"submitterId": '123',
#                  'objectId': '2222',
#                  'archived': None,
#                  'entityId': "syn2222"},
#                 {"submitterId": '234',
#                  'objectId': '5555',
#                  'archived': None,
#                  'entityId': "syn2222"}]

#     submissions = [{"submitterId": '123',
#                     'objectId': '3333'},
#                    {"submitterId": '234',
#                     'objectId': '4444'}]

#     firstquery = ("select objectId, submitterId, entityId, archived from "
#                   "evaluation_2 where prediction_file_status == 'VALIDATED'")

#     secondquery = ("select objectId, submitterId from evaluation_3 "
#                    "where prediction_file_status == 'SCORED'")
#     with patch.object(challengeutils.utils,
#                       "evaluation_queue_query",
#                       side_effect=[writeups,
#                                    submissions]) as patch_query,\
#          patch.object(challengeutils.project_submission,
#                       "attach_writeup_to_main_submission") as patch_attach:
#         archive_and_attach_writeups(SYN, '2', '3',
#                                     status_key="prediction_file_status")
#         assert patch_query.call_count == 2
#         calls = [mock.call(SYN, firstquery), mock.call(SYN, secondquery)]
#         patch_query.assert_has_calls(calls)
#         assert patch_attach.call_count == 2
