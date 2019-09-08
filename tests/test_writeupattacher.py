'''
Testing writeup attacher
'''
import time
from mock import patch
import synapseclient
import synapseutils

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

# def test_archive_writeup():
#     with patch.object(syn, "getSubmission"
#                       return_value=SUBMISSION) as patch_getsub,\
#          patch.object(syn, "getSubmissionStatus") as patch_getsubstatus,\
#          patch.object(challengeutils.writeup_attacher,
#                       "_create_archive_writeup"
#                       return_value=ENTITY) as patch_syn_copy,\
#          patch.object(challengeutils.utils
#                       "update_single_submission_status"):
#         archive_proj = archive_writeup(syn, SUBMISSION.id)
