"""Testing writeup attacher"""
import time
import mock
from mock import patch
import pandas as pd
import synapseclient
from synapseclient.annotations import to_submission_status_annotations


import challengeutils.utils
import challengeutils.project_submission

SYN = mock.create_autospec(synapseclient.Synapse)
ENTITY = synapseclient.File(name='test', parentId="syn123", id="syn222")
SUBMISSION = synapseclient.Submission(name="wow", entityId=ENTITY['id'],
                                      evaluationId="123", versionNumber=2,
                                      entity=ENTITY, id=333)

SUB_ANNOTATIONS = to_submission_status_annotations({"test": "1"})
SUB_STATUS = synapseclient.SubmissionStatus(annotations=SUB_ANNOTATIONS)
WRITEUP_QUEUEID = '2'
SUBMISSION_QUEUEID = '3'

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
