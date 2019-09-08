'''
Testing writeup attacher
'''
import time
import mock
import synapseclient
import synapseutils

import challengeutils.writeup_attacher
from challengeutils.writeup_attacher import _create_archive_writeup


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
    with mock.patch.object(syn, "store",
                           return_value=return_project) as patch_syn_store,\
         mock.patch.object(time, "time", return_value=10),\
         mock.patch.object(synapseutils, "copy") as patch_syn_copy:
        archive_proj = _create_archive_writeup(syn, SUBMISSION)
        assert archive_proj == return_project
        patch_syn_store.assert_called_once_with(project)
        patch_syn_copy.assert_called_once_with(syn, SUBMISSION.entityId,
                                               archive_proj.id)
