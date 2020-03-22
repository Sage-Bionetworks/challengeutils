"""Testing writeup attacher"""
import time
import mock
from mock import patch
import pandas as pd
import synapseclient
from synapseclient.annotations import to_submission_status_annotations


import challengeutils.utils
import challengeutils.project_submission
from challengeutils.project_submission import join_evaluations



SYN = mock.create_autospec(synapseclient.Synapse)
ENTITY = synapseclient.File(name='test', parentId="syn123", id="syn222")
SUBMISSION = synapseclient.Submission(name="wow", entityId=ENTITY['id'],
                                      evaluationId="123", versionNumber=2,
                                      entity=ENTITY, id=333)

SUB_ANNOTATIONS = to_submission_status_annotations({"test": "1"})
SUB_STATUS = synapseclient.SubmissionStatus(annotations=SUB_ANNOTATIONS)
WRITEUP_QUEUEID = '2'
SUBMISSION_QUEUEID = '3'

# def test__archive_project_submission():
#     """Create archive project submission"""
#     archived_name = (f"Archived {SUBMISSION.entity.name} 10000 "
#                      f"{SUBMISSION.id} {SUBMISSION.entityId}")
#     # This 'project' is used for the assert call
#     project = synapseclient.Project(archived_name)
#     # The returned project must have id as the id is used in copy call
#     return_project = synapseclient.Project(archived_name, id="syn888")
#     # The time value is multipled by 1000
#     with patch.object(time, "time", return_value=10), \
#          patch.object(challengeutils.utils,
#                       "copy_project",
#                       return_value=return_project) as patch_create:
#         archive_proj = _archive_project_submission(SYN, SUBMISSION)
#         assert archive_proj == return_project
#         patch_create.assert_called_once_with(SYN, SUBMISSION.entityId,
#                                              archived_name)


# def test_alreadyarchived_archive_project():
#     """
#     If the archive annotation already exists the project submission shouldn't
#     be archived, making sure that the archived entity id is returned.
#     """
#     annotations = {"archived": "1"}
#     syn_annots = to_submission_status_annotations(annotations)
#     submission_status = synapseclient.SubmissionStatus(annotations=syn_annots)
#     with patch.object(SYN, "getSubmission",
#                       return_value=SUBMISSION) as patch_getsub,\
#          patch.object(SYN, "getSubmissionStatus",
#                       return_value=submission_status) as patch_getsubstatus,\
#          patch.object(challengeutils.project_submission,
#                       "_archive_project_submission") as patch__archive,\
#          patch.object(challengeutils.utils,
#                       "update_single_submission_status") as patch_update,\
#          patch.object(SYN, "store") as patch_syn_store:
#         archive_proj = archive_project_submission(SYN, SUBMISSION.id)
#         patch_getsub.assert_called_once_with(SUBMISSION.id, downloadFile=False)
#         patch_getsubstatus.assert_called_once_with(SUBMISSION.id)
#         patch__archive.assert_not_called()
#         patch_update.assert_not_called()
#         patch_syn_store.assert_not_called()
#         # The archive project entity id should be returned
#         assert archive_proj == annotations['archived']


# def test_notarchive_archive_project_submission():
#     """Archive project submission if there is not an archive"""
#     return_project = synapseclient.Project("test", id="syn2222")
#     annotations = {"archived": "syn2222"}
#     syn_annots = to_submission_status_annotations(annotations)
#     archive_substatus = synapseclient.SubmissionStatus(annotations=syn_annots)
#     with patch.object(SYN, "getSubmission",
#                       return_value=SUBMISSION) as patch_getsub,\
#          patch.object(SYN, "getSubmissionStatus",
#                       return_value=archive_substatus) as patch_getsubstatus,\
#          patch.object(challengeutils.project_submission,
#                       "_archive_project_submission",
#                       return_value=return_project) as patch__archive,\
#          patch.object(challengeutils.utils,
#                       "update_single_submission_status",
#                       return_value=archive_substatus) as patch_update,\
#          patch.object(SYN, "store") as patch_syn_store:
#         archive_proj = archive_project_submission(SYN, SUBMISSION.id,
#                                                   rearchive=True)
#         patch_getsub.assert_called_once_with(SUBMISSION.id, downloadFile=False)
#         patch_getsubstatus.assert_called_once_with(SUBMISSION.id)
#         patch__archive.assert_called_once_with(SYN, SUBMISSION)
#         patch_update.assert_called_once_with(archive_substatus,
#                                              annotations)
#         patch_syn_store.assert_called_once_with(archive_substatus)
#         assert archive_proj == return_project.id


# def test_forcerearchive_archive_project_submission():
#     """
#     Archive project submission even if there is already an archive but
#     rearchive=True
#     """
#     submission_status = synapseclient.SubmissionStatus(annotations={})
#     return_project = synapseclient.Project("test", id="syn2222")
#     annotations = {"archived": "syn2222"}
#     syn_annots = to_submission_status_annotations(annotations)
#     archive_substatus = synapseclient.SubmissionStatus(annotations=syn_annots)
#     with patch.object(SYN, "getSubmission",
#                       return_value=SUBMISSION) as patch_getsub,\
#          patch.object(SYN, "getSubmissionStatus",
#                       return_value=submission_status) as patch_getsubstatus,\
#          patch.object(challengeutils.project_submission,
#                       "_archive_project_submission",
#                       return_value=return_project) as patch__archive,\
#          patch.object(challengeutils.utils,
#                       "update_single_submission_status",
#                       return_value=archive_substatus) as patch_update,\
#          patch.object(SYN, "store") as patch_syn_store:
#         archive_proj = archive_project_submission(SYN, SUBMISSION.id)
#         patch_getsub.assert_called_once_with(SUBMISSION.id, downloadFile=False)
#         patch_getsubstatus.assert_called_once_with(SUBMISSION.id)
#         patch__archive.assert_called_once_with(SYN, SUBMISSION)
#         patch_update.assert_called_once_with(submission_status,
#                                              annotations)
#         patch_syn_store.assert_called_once_with(archive_substatus)
#         assert archive_proj == return_project.id


# def test_default_params_archive_project_submissions():
#     """Archive project submissions given evaluation queue"""
#     eval_obj = synapseclient.Evaluation(id=1234, contentSource="syn123",
#                                         name="test")
#     query = "select objectId from evaluation_1234 where STATUS == 'VALIDATED'"
#     query_results = [{'objectId': SUBMISSION.id}]
#     with patch.object(challengeutils.utils, "evaluation_queue_query",
#                       return_value=query_results) as patch_query,\
#          patch.object(challengeutils.project_submission,
#                       "archive_project_submission",
#                       return_value="syn1234") as patch_archive:
#         archived = archive_project_submissions(SYN, eval_obj.id)
#         patch_query.assert_called_once_with(SYN, query)
#         patch_archive.assert_called_once_with(SYN, SUBMISSION.id,
#                                               rearchive=False)
#         assert archived == ['syn1234']


# def test_nondefault_params_archive_project_submissions():
#     """Archive project submissions given evaluation queue with non default
#     params"""
#     eval_obj = synapseclient.Evaluation(id=1234, contentSource="syn123",
#                                         name="test")
#     query = "select objectId from evaluation_1234 where prediction == 'SCORED'"
#     query_results = [{'objectId': SUBMISSION.id}]
#     with patch.object(challengeutils.utils, "evaluation_queue_query",
#                       return_value=query_results) as patch_query,\
#          patch.object(challengeutils.project_submission,
#                       "archive_project_submission",
#                       return_value="syn1234") as patch_archive:
#         archived = archive_project_submissions(SYN, eval_obj,
#                                                status_key="prediction",
#                                                status="SCORED",
#                                                rearchive=True)
#         patch_query.assert_called_once_with(SYN, query)
#         patch_archive.assert_called_once_with(SYN, SUBMISSION.id,
#                                               rearchive=True)
#         assert archived == ['syn1234']


# def test_multiple_submissions_archive_project_submissions():
#     """
#     Archive project submissions given evaluation queue that has multiple
#     submissions
#     """
#     eval_obj = synapseclient.Evaluation(id=1234, contentSource="syn123",
#                                         name="test")
#     query_results = [{'objectId': SUBMISSION.id}, {'objectId': SUBMISSION.id}]
#     query = "select objectId from evaluation_1234 where STATUS == 'VALIDATED'"

#     with patch.object(challengeutils.utils, "evaluation_queue_query",
#                       return_value=query_results) as patch_query,\
#          patch.object(challengeutils.project_submission,
#                       "archive_project_submission",
#                       return_value="syn1234") as patch_archive:
#         archived = archive_project_submissions(SYN, eval_obj)
#         patch_query.assert_called_once_with(SYN, query)
#         assert patch_archive.call_count == 2
#         assert archived == ['syn1234', 'syn1234']


# def test_archive_and_attach_project_submissions():
#     """Archive and attach writeups"""
#     expected_dict = [{'submitterId': '123',
#                       'STATUS_y': 'VALIDATED',
#                       'STATUS_x': 'SCORED',
#                       'entityId_y': 'syn1234',
#                       'archived': 'syn3333',
#                       'objectId_x': '2222',
#                       'objectId_y': '3333'},
#                      {'submitterId': '234',
#                       'STATUS_y': 'VALIDATED',
#                       'STATUS_x': 'SCORED',
#                       'entityId_y': 'syn2333',
#                       'archived': 'syn4444',
#                       'objectId_x': '5555',
#                       'objectId_y': '4444'}]
#     expecteddf = pd.DataFrame(expected_dict)
#     with patch.object(challengeutils.project_submission,
#                       "archive_project_submissions") as patch_archive,\
#          patch.object(challengeutils.project_submission,
#                       "join_evaluations",
#                       return_value=expecteddf) as patch_join,\
#          patch.object(challengeutils.utils,
#                       "annotate_submission") as patch_annotate:
#         archive_and_attach_project_submissions(SYN, WRITEUP_QUEUEID,
#                                                SUBMISSION_QUEUEID)
#         patch_archive.assert_called_once_with(SYN, WRITEUP_QUEUEID,
#                                               status_key="STATUS",
#                                               status="VALIDATED",
#                                               rearchive=False)
#         patch_join.assert_called_once_with(SYN, SUBMISSION_QUEUEID,
#                                            WRITEUP_QUEUEID,
#                                            joinby="submitterId",
#                                            how="left")
#         assert patch_annotate.call_count == 2
#         calls = [mock.call(SYN, '2222', {'writeUp': 'syn1234',
#                                          'archivedWriteUp': 'syn3333'},
#                            ['writeUp', 'archivedWriteUp']),
#                  mock.call(SYN, '5555', {'writeUp': 'syn2333',
#                                          'archivedWriteUp': 'syn4444'},
#                            ['writeUp', 'archivedWriteUp'])]
#         patch_annotate.assert_has_calls(calls, any_order=True)


# def test_statuskey_archive_and_attach_writeups():
#     """Archive and attach writeups"""
#     expected_dict = [{'submitterId': '123',
#                       'prediction_file_status_y': 'VALIDATED',
#                       'prediction_file_status_x': 'SCORED',
#                       'entityId_y': 'syn1234',
#                       'archived': 'syn3333',
#                       'objectId_x': '2222',
#                       'objectId_y': '3333'},
#                      {'submitterId': '234',
#                       'prediction_file_status_y': 'VALIDATED',
#                       'prediction_file_status_x': 'SCORED',
#                       'entityId_y': 'syn2333',
#                       'archived': 'syn4444',
#                       'objectId_x': '5555',
#                       'objectId_y': '4444'}]
#     expecteddf = pd.DataFrame(expected_dict)
#     with patch.object(challengeutils.project_submission,
#                       "archive_project_submissions") as patch_archive,\
#          patch.object(challengeutils.project_submission,
#                       "join_evaluations",
#                       return_value=expecteddf) as patch_join,\
#          patch.object(challengeutils.utils,
#                       "annotate_submission") as patch_annotate:
#         archive_and_attach_project_submissions(SYN, WRITEUP_QUEUEID,
#                                                SUBMISSION_QUEUEID,
#                                                status_key="prediction_file_status")
#         patch_archive.assert_called_once_with(SYN, WRITEUP_QUEUEID,
#                                               status_key="prediction_file_status",
#                                               status="VALIDATED",
#                                               rearchive=False)
#         patch_join.assert_called_once_with(SYN, SUBMISSION_QUEUEID,
#                                            WRITEUP_QUEUEID,
#                                            joinby="submitterId",
#                                            how="left")
#         assert patch_annotate.call_count == 2
#         calls = [mock.call(SYN, '2222', {'writeUp': 'syn1234',
#                                          'archivedWriteUp': 'syn3333'},
#                            ['writeUp', 'archivedWriteUp']),
#                  mock.call(SYN, '5555', {'writeUp': 'syn2333',
#                                          'archivedWriteUp': 'syn4444'},
#                            ['writeUp', 'archivedWriteUp'])]
#         patch_annotate.assert_has_calls(calls, any_order=True)
