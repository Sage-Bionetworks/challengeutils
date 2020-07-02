'''
Test challengeutils.discussion functions
'''
import json
from unittest import mock
from unittest.mock import patch
import uuid

import requests
import synapseclient

from challengeutils import discussion
from challengeutils.discussion import DiscussionApi
from challengeutils.synapseservices.discussion import Forum, Thread, Reply

syn = mock.create_autospec(synapseclient.Synapse)
api = DiscussionApi(syn)

PROJECTID = "syn100000"
FORUM_DICT = {'etag': 'foo',
              'id': '444',
              'projectId': PROJECTID}
FORUM_OBJ = Forum(**FORUM_DICT)
THREAD_DICT = {
    'messageKey': str(uuid.uuid1()),
    'numberOfReplies': 0,
    'isPinned': False,
    'numberOfViews': 0,
    'activeAuthors': ['2222', '2222'],
    'isEdited': False,
    'title': 'titlehere',
    'createdOn': '2019-06-27T04:01:25.000Z',
    'modifiedOn': '2019-06-27T04:01:25.000Z',
    'isDeleted': False,
    'createdBy': str(uuid.uuid1()),
    'etag': 'dfsdf-df-4a44dfsd-982c-2d81102cf5d6',
    'lastActivity': '2019-06-27T04:01:25.000Z',
    'id': '5583',
    'projectId': PROJECTID,
    'forumId': FORUM_OBJ.id
}
THREAD_OBJ = Thread(**THREAD_DICT)
REPLY_DICT = {
    'threadId': THREAD_OBJ.id,
    'messageKey': str(uuid.uuid1()),
    'modifiedOn': '2019-06-27T04:07:56.000Z',
    'isDeleted': False,
    'createdBy': '333',
    'etag': 'sdf-1e89-4c84-dsf-sdfsdf',
    'isEdited': False,
    'id': str(uuid.uuid1()),
    'projectId': PROJECTID,
    'createdOn': '2019-06-27T04:07:56.000Z',
    'forumId': FORUM_OBJ.id
}
REPLY_OBJ = Reply(**REPLY_DICT)


class TextResponseMock:
    '''
    This is to mock the request.get text
    '''
    text = "text"


def test__get_project_forum():
    '''
    Test getting forum object
    '''
    with mock.patch.object(syn, "restGET",
                           return_value=FORUM_DICT) as patch_syn_restget:
        forum = api.get_project_forum(PROJECTID)
        assert forum == FORUM_OBJ
        patch_syn_restget.assert_called_once_with(
            '/project/{}/forum'.format(PROJECTID))


def test_get_forum_threads():
    '''
    Test get forum threads
    '''
    response = [THREAD_OBJ]
    with mock.patch.object(DiscussionApi,
                           "get_project_forum",
                           return_value=FORUM_OBJ) as patch_get_obj,\
        mock.patch.object(DiscussionApi,
                          "get_forum_threads",
                          return_value=response) as patch_syn_get:
        threads = discussion.get_forum_threads(syn, PROJECTID)
        patch_get_obj.assert_called_once_with(PROJECTID)
        patch_syn_get.assert_called_once_with(FORUM_OBJ.id)
        # Although actual return isn't a string, this test just makes sure that
        # that the result from _GET_Paginated is returned
        assert threads == response


def test_get_thread_replies():
    '''
    Test get forum threads
    '''
    response = [REPLY_DICT]
    with mock.patch.object(syn, "_GET_paginated",
                           return_value=response) as patch_syn_get:
        replies = api.get_thread_replies(222)
        replies = list(replies)
        patch_syn_get.assert_called_once_with(
            '/thread/222/replies?filter=EXCLUDE_DELETED'
        )
        # Although actual return isn't a string, this test just makes sure that
        # that the result from _GET_Paginated is returned
        assert replies == [REPLY_OBJ]


def test__get_text():
    '''Test get text'''
    response = "response"
    text_url = {'messageUrl': 'foo?wowthisworks'}
    with mock.patch.object(requests, "get",
                           return_value=response) as patch_requestget:
        text = discussion._get_text(text_url)
        patch_requestget.assert_called_once_with("foo")
        # Although actual return isn't a string, this test just makes sure that
        # that the result from request.get is returned
        assert text == response


def test_get_thread_text_threadobj():
    '''Test get thread text'''
    with mock.patch.object(DiscussionApi,
                           "get_thread_message_url",
                           return_value='wwwww') as patch_get_url,\
        mock.patch.object(discussion,
                          "_get_text",
                          return_value=TextResponseMock) as patch_get_text:
        thread_text = discussion.get_thread_text(syn, THREAD_OBJ)
        patch_get_url.assert_called_once_with(THREAD_OBJ.messagekey)
        assert thread_text == 'text'
        patch_get_text.assert_called_once_with('wwwww')


def test_get_thread_text_threadid():
    '''Test get thread text'''
    with mock.patch.object(DiscussionApi,
                           "get_thread",
                           return_value=THREAD_OBJ) as patch_get_thread,\
         mock.patch.object(DiscussionApi,
                           "get_thread_message_url",
                           return_value='wwwww') as patch_get_url,\
         mock.patch.object(discussion,
                           "_get_text",
                           return_value=TextResponseMock) as patch_get_text:
        thread_text = discussion.get_thread_text(syn, THREAD_OBJ.id)
        patch_get_thread.assert_called_once_with(THREAD_OBJ.id)
        patch_get_url.assert_called_once_with(THREAD_OBJ.messagekey)
        assert thread_text == 'text'
        patch_get_text.assert_called_once_with('wwwww')


def test_get_thread_reply_text_replyobj():
    '''Test get thread reply with reply object'''
    with mock.patch.object(DiscussionApi,
                           "get_reply_message_url",
                           return_value='wwwww') as patch_get_url,\
        mock.patch.object(discussion,
                          "_get_text",
                          return_value=TextResponseMock) as patch_get_text:
        thread_text = discussion.get_thread_reply_text(syn, REPLY_OBJ)
        patch_get_url.assert_called_once_with(REPLY_OBJ.messagekey)
        assert thread_text == 'text'
        patch_get_text.assert_called_once_with('wwwww')


def test_get_thread_reply_text_replyid():
    '''Test get thread reply with reply id'''
    with mock.patch.object(DiscussionApi,
                           "get_reply",
                           return_value=REPLY_OBJ) as patch_get_reply,\
         mock.patch.object(DiscussionApi,
                           "get_reply_message_url",
                           return_value='wwwww') as patch_get_url,\
         mock.patch.object(discussion,
                           "_get_text",
                           return_value=TextResponseMock) as patch_get_text:
        thread_text = discussion.get_thread_reply_text(syn, REPLY_OBJ.id)
        patch_get_reply.assert_called_once_with(REPLY_OBJ.id)
        patch_get_url.assert_called_once_with(REPLY_OBJ.messagekey)
        assert thread_text == 'text'
        patch_get_text.assert_called_once_with('wwwww')


def test_get_forum_participants():
    '''Test get forum participants'''
    threads = [THREAD_OBJ]
    profile = synapseclient.UserProfile(ownerId="test")
    with mock.patch.object(discussion,
                           "get_forum_threads",
                           return_value=threads) as patch_get_threads,\
         mock.patch.object(syn,
                           "getUserProfile",
                           return_value=profile) as patch_getuserprofile:
        participants = discussion.get_forum_participants(syn, PROJECTID)
        patch_get_threads.assert_called_once_with(syn, PROJECTID)
        patch_getuserprofile.assert_called_once_with('2222')
        assert participants == [profile]


def test_create_thread():
    '''Test thread creation'''
    title = "my title here"
    message = "my message here"
    with mock.patch.object(DiscussionApi,
                           "get_project_forum",
                           return_value=FORUM_OBJ) as patch_get_obj,\
         mock.patch.object(DiscussionApi, "post_thread",
                           return_value=THREAD_OBJ) as patch_post:
        threadobj = discussion.create_thread(syn, PROJECTID, title, message)
        patch_get_obj.assert_called_once_with(PROJECTID)
        patch_post.assert_called_once_with(
            FORUM_OBJ.id, title, message
        )
        assert threadobj == THREAD_OBJ


def test_create_thread_reply():
    '''test Create thread reply'''
    message = "my message here"
    thread_reply_dict = {'threadId': THREAD_OBJ.id,
                         'messageMarkdown': message}
    with mock.patch.object(syn, "restPOST",
                           return_value=REPLY_DICT) as patch_get_obj:
        replyobj = api.post_reply(THREAD_OBJ.id, message)
        patch_get_obj.assert_called_once_with(
            '/reply', body=json.dumps(thread_reply_dict))
        assert replyobj == REPLY_OBJ


def test_get_threads_referencing_entity():
    '''Test getting entity thread associations'''
    response = [THREAD_DICT]
    with mock.patch.object(syn, "_GET_paginated",
                           return_value=response) as patch_syn_get:
        entity_threads = api.get_threads_referencing_entity(PROJECTID)
        entity_threads = list(entity_threads)
        uri = f"/entity/{PROJECTID}/threads"
        patch_syn_get.assert_called_once_with(uri)
        # Although actual return isn't a string, this test just makes sure that
        # that the result from _GET_Paginated is returned
        assert entity_threads == [THREAD_OBJ]


def test__copy_thread():
    """Tests copying of threads"""
    profile = synapseclient.UserProfile(ownerId="test",
                                        userName="foobar")
    thread_text = str(uuid.uuid1())
    on_behalf_of = "On behalf of @{user}\n\n".format(user=profile.userName)
    new_thread_text = on_behalf_of + thread_text

    with mock.patch.object(syn, "getUserProfile",
                           return_value=profile) as patch_getuserprofile,\
         mock.patch.object(discussion, "get_thread_text",
                           return_value=thread_text) as patch_thread_text,\
         mock.patch.object(discussion, "create_thread",
                           return_value=THREAD_OBJ) as patch_create_thread:
        thread = discussion._copy_thread(syn, THREAD_OBJ, PROJECTID)
        patch_getuserprofile.assert_called_once_with(THREAD_OBJ.createdby)
        patch_thread_text.assert_called_once_with(syn, THREAD_OBJ)
        patch_create_thread.assert_called_once_with(syn, PROJECTID,
                                                    THREAD_OBJ.title,
                                                    new_thread_text)
        assert thread == THREAD_OBJ


def test_copy_thread():
    """Tests copying thread and replies"""
    with patch.object(discussion, "_copy_thread",
                      return_value=THREAD_OBJ) as patch_copy_threads,\
         patch.object(discussion, "get_thread_replies",
                      return_value=[REPLY_OBJ]) as patch_thread_replies,\
         patch.object(discussion, "copy_reply") as patch_copy_reply:
        discussion.copy_thread(syn, THREAD_OBJ, PROJECTID)
        patch_copy_threads.assert_called_once_with(syn, THREAD_OBJ, PROJECTID)
        patch_thread_replies.assert_called_once_with(syn, THREAD_OBJ.id)
        patch_copy_reply.assert_called_once_with(syn, REPLY_OBJ,
                                                 THREAD_OBJ.id)


def test_copy_reply():
    """Tests copying of replies"""
    profile = synapseclient.UserProfile(ownerId="test",
                                        userName="foobar")
    reply_text = str(uuid.uuid1())
    on_behalf_of = "On behalf of @{user}\n\n".format(user=profile.userName)
    new_reply_text = on_behalf_of + reply_text

    with mock.patch.object(syn, "getUserProfile",
                           return_value=profile) as patch_getuserprofile,\
         mock.patch.object(discussion, "get_thread_reply_text",
                           return_value=reply_text) as patch_reply_text,\
         mock.patch.object(discussion, "create_thread_reply",
                           return_value=REPLY_OBJ) as patch_create_reply:
        reply = discussion.copy_reply(syn, REPLY_OBJ, THREAD_OBJ)
        patch_getuserprofile.assert_called_once_with(REPLY_OBJ.createdby)
        patch_reply_text.assert_called_once_with(syn, REPLY_OBJ)
        patch_create_reply.assert_called_once_with(syn, THREAD_OBJ.id,
                                                   new_reply_text)
        assert reply == REPLY_OBJ


def test_copy_forum():
    """Tests copying of entire forum"""
    new_thread = THREAD_OBJ
    new_thread.id = str(uuid.uuid1())
    new_projectid = str(uuid.uuid1())
    with mock.patch.object(discussion, "get_forum_threads",
                           return_value=[THREAD_OBJ]) as patch_get_threads,\
         mock.patch.object(discussion, "copy_thread",
                           return_value=new_thread) as patch_copy_thread:
        discussion.copy_forum(syn, PROJECTID, new_projectid)
        patch_get_threads.assert_called_once_with(syn, PROJECTID)
        patch_copy_thread.assert_called_once_with(syn, THREAD_OBJ,
                                                  new_projectid)
