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
    with mock.patch.object(discussion,
                           "_get_forum_obj",
                           return_value=FORUM_OBJ) as patch_get_obj,\
        mock.patch.object(syn,
                          "_GET_paginated") as patch_syn_get:
        discussion.get_forum_threads(syn, PROJECTID)
        patch_get_obj.assert_called_once_with(syn, PROJECTID)
        patch_syn_get.assert_called_once_with(
            '/forum/{forumid}/threads?filter={query_filter}'.format(
                forumid=FORUM_OBJ['id'], query_filter="EXCLUDE_DELETED"),
            limit=20, offset=0)
