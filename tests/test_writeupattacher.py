'''
Testing writeup attacher
'''
import time
import mock
import synapseclient

import challengeutils.writeup_attacher
from challengeutils.writeup_attacher import _create_archive_writeup_project


syn = synapseclient.Synapse()
ENTITY = synapseclient.File(name='test', parentId="syn123", id="syn222")
SUBMISSION = synapseclient.Submission(name="wow", entityId=ENTITY['id'],
                                      evaluationId="123", versionNumber=2,
                                      entity=ENTITY, id=333)


def test__create_archive_writeup_project():
    '''
    Test creation of writeup project
    '''
    archived_name = (f"Archived {SUBMISSION.entity.name} 10000 "
                     f"{SUBMISSION.id} {SUBMISSION.entityId}")
    project = synapseclient.Project(archived_name)
    with mock.patch.object(syn, "store",
                           return_value=ENTITY) as patch_syn_store,\
         mock.patch.object(time, "time", return_value=10):
        entity = _create_archive_writeup_project(syn, SUBMISSION)
        assert entity == ENTITY
        patch_syn_store.assert_called_once_with(project)
