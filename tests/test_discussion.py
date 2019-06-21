import synapseclient
import mock
from challengeutils import discussion
syn = synapseclient.Synapse()
PROJECTID = "syn100000"
FORUM_OBJ = {'etag': 'foo',
             'id': '444',
             'projectId': PROJECTID}


def test__get_forum_obj():
    '''
    Test getting forum object
    '''
    with mock.patch.object(syn, "restGET",
                           return_value=FORUM_OBJ) as patch_syn_restget:
        forum = discussion._get_forum_obj(syn, PROJECTID)
        assert forum == FORUM_OBJ
        patch_syn_restget.assert_called_once_with(
            '/project/{}/forum'.format(PROJECTID))


def test_get_forum_threads():
    '''
    Test get forum threads
    '''
    with mock.patch.object(discussion, "_get_forum_obj") as patch_get_obj:
        
