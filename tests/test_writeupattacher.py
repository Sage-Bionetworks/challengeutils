'''
Testing writeup attacher
'''
import time
from mock import patch
import synapseclient
import synapseutils
from synapseclient.annotations import to_submission_status_annotations

import challengeutils.utils
import challengeutils.writeup_attacher
from challengeutils.writeup_attacher import _create_archive_writeup
from challengeutils.writeup_attacher import archive_writeup


syn = synapseclient.Synapse()
ENTITY = synapseclient.File(name='test', parentId="syn123", id="syn222")
SUBMISSION = synapseclient.Submission(name="wow", entityId=ENTITY['id'],
                                      evaluationId="123", versionNumber=2,
                                      entity=ENTITY, id=333)


def test__create_archive_writeup():
    '''
    Test creation of writeup project
    '''
    archived_name = (f"Archived {SUBMISSION.entity.name} 10000 "
                     f"{SUBMISSION.id} {SUBMISSION.entityId}")
    # This 'project' is used for the assert call
    project = synapseclient.Project(archived_name)
    # The returned project must have id as the id is used in copy call
    return_project = synapseclient.Project(archived_name, id="syn888")
    with patch.object(syn, "store",
                      return_value=return_project) as patch_syn_store,\
         patch.object(time, "time", return_value=10),\
         patch.object(synapseutils, "copy") as patch_syn_copy:
        archive_proj = _create_archive_writeup(syn, SUBMISSION)
        assert archive_proj == return_project
        patch_syn_store.assert_called_once_with(project)
        patch_syn_copy.assert_called_once_with(syn, SUBMISSION.entityId,
                                               archive_proj.id)

def test_alreadyarchived_archive_writeup():
    '''
    Test archive writeup if the archive annotation already exists
    the project shouldn't be copied
    '''
    annotations = {"archived": "1"}
    syn_annots = to_submission_status_annotations(annotations)
    submission_status = synapseclient.SubmissionStatus(annotations=syn_annots)
    with patch.object(syn, "getSubmission",
                      return_value=SUBMISSION) as patch_getsub,\
         patch.object(syn, "getSubmissionStatus",
                      return_value=submission_status) as patch_getsubstatus,\
         patch.object(challengeutils.writeup_attacher,
                      "_create_archive_writeup") as patch__archive,\
         patch.object(challengeutils.utils,
                      "update_single_submission_status") as patch_update,\
         patch.object(syn, "store") as patch_syn_store:
        archive_proj = archive_writeup(syn, SUBMISSION.id)
        patch_getsub.assert_called_once_with(SUBMISSION.id, downloadFile=False)
        patch_getsubstatus.assert_called_once_with(SUBMISSION.id)
        patch__archive.assert_not_called()
        patch_update.assert_not_called()
        patch_syn_store.assert_not_called()
        assert archive_proj is None


def test_notarchive_archive_writeup():
    '''
    Test archive writeup if there is not an archive
    '''
    return_project = synapseclient.Project("test", id="syn2222")
    annotations = {"archived": "syn2222"}
    syn_annots = to_submission_status_annotations(annotations)
    archive_substatus = synapseclient.SubmissionStatus(annotations=syn_annots)
    with patch.object(syn, "getSubmission",
                      return_value=SUBMISSION) as patch_getsub,\
         patch.object(syn, "getSubmissionStatus",
                      return_value=archive_substatus) as patch_getsubstatus,\
         patch.object(challengeutils.writeup_attacher,
                      "_create_archive_writeup",
                      return_value=return_project) as patch__archive,\
         patch.object(challengeutils.utils,
                      "update_single_submission_status",
                      return_value=archive_substatus) as patch_update,\
         patch.object(syn, "store") as patch_syn_store:
        archive_proj = archive_writeup(syn, SUBMISSION.id, rearchive=True)
        patch_getsub.assert_called_once_with(SUBMISSION.id, downloadFile=False)
        patch_getsubstatus.assert_called_once_with(SUBMISSION.id)
        patch__archive.assert_called_once_with(syn, SUBMISSION)
        patch_update.assert_called_once_with(archive_substatus,
                                             annotations)
        patch_syn_store.assert_called_once_with(archive_substatus)
        assert archive_proj == return_project.id


def test_forcerearchive_archive_writeup():
    '''
    Test archive writeup if there is already an archive but
    rearchive=True
    '''
    submission_status = synapseclient.SubmissionStatus(annotations={})
    return_project = synapseclient.Project("test", id="syn2222")
    annotations = {"archived": "syn2222"}
    syn_annots = to_submission_status_annotations(annotations)
    archive_substatus = synapseclient.SubmissionStatus(annotations=syn_annots)
    with patch.object(syn, "getSubmission",
                      return_value=SUBMISSION) as patch_getsub,\
         patch.object(syn, "getSubmissionStatus",
                      return_value=submission_status) as patch_getsubstatus,\
         patch.object(challengeutils.writeup_attacher,
                      "_create_archive_writeup",
                      return_value=return_project) as patch__archive,\
         patch.object(challengeutils.utils,
                      "update_single_submission_status",
                      return_value=archive_substatus) as patch_update,\
         patch.object(syn, "store") as patch_syn_store:
        archive_proj = archive_writeup(syn, SUBMISSION.id)
        patch_getsub.assert_called_once_with(SUBMISSION.id, downloadFile=False)
        patch_getsubstatus.assert_called_once_with(SUBMISSION.id)
        patch__archive.assert_called_once_with(syn, SUBMISSION)
        patch_update.assert_called_once_with(submission_status,
                                             annotations)
        patch_syn_store.assert_called_once_with(archive_substatus)
        assert archive_proj == return_project.id