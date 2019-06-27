import json
import mock
import requests
import challengeutils.discussion
import synapseclient
syn = synapseclient.Synapse()
PROJECTID = "syn100000"
FORUM_OBJ = {'etag': 'foo',
             'id': '444',
             'projectId': PROJECTID}
THREAD_OBJ = {'messageKey': '333/3333/22222-5d2224e-222-222-2222sdfasdf',
              'numberOfReplies': 0,
              'isPinned': False,
              'numberOfViews': 0,
              'activeAuthors': ['2222', '2222'],
              'isEdited': False,
              'title': 'titlehere',
              'createdOn': '2019-06-27T04:01:25.000Z',
              'modifiedOn': '2019-06-27T04:01:25.000Z',
              'isDeleted': False,
              'createdBy': '222',
              'etag': 'dfsdf-df-4a44dfsd-982c-2d81102cf5d6',
              'lastActivity': '2019-06-27T04:01:25.000Z',
              'id': '5583',
              'projectId': PROJECTID,
              'forumId': FORUM_OBJ['id']}
REPLY_OBJ = {'threadId': THREAD_OBJ['id'],
             'messageKey': '222/2222/22222/2222-5b222f4-4a62-bde7-2222222',
             'modifiedOn': '2019-06-27T04:07:56.000Z',
             'isDeleted': False,
             'createdBy': '222',
             'etag': 'sdf-1e89-4c84-dsf-sdfsdf',
             'isEdited': False,
             'id': '18763',
             'projectId': PROJECTID,
             'createdOn': '2019-06-27T04:07:56.000Z',
             'forumId': FORUM_OBJ['id']}


class TEXT_RESPONSE_MOCK:
    '''
    This is to mock the request.get text
    '''
    text = "text"


def test__get_forum_obj():
    '''
    Test getting forum object
    '''
    with mock.patch.object(syn, "restGET",
                           return_value=FORUM_OBJ) as patch_syn_restget:
        forum = challengeutils.discussion._get_forum_obj(syn, PROJECTID)
        assert forum == FORUM_OBJ
        patch_syn_restget.assert_called_once_with(
            '/project/{}/forum'.format(PROJECTID))


def test_get_forum_threads():
    '''
    Test get forum threads
    '''
    response = [THREAD_OBJ]
    with mock.patch.object(challengeutils.discussion,
                           "_get_forum_obj",
                           return_value=FORUM_OBJ) as patch_get_obj,\
        mock.patch.object(syn,
                          "_GET_paginated", return_value=response) as patch_syn_get:
        threads = challengeutils.discussion.get_forum_threads(syn, PROJECTID)
        patch_get_obj.assert_called_once_with(syn, PROJECTID)
        patch_syn_get.assert_called_once_with(
            '/forum/{forumid}/threads?filter={query_filter}'.format(
                forumid=FORUM_OBJ['id'], query_filter="EXCLUDE_DELETED"),
            limit=20, offset=0)
        # Although actual return isn't a string, this test just makes sure that
        # that the result from _GET_Paginated is returned
        assert threads == response


def test_get_thread_replies():
    '''
    Test get forum threads
    '''
    response = [REPLY_OBJ]
    with mock.patch.object(syn,
                           "_GET_paginated", return_value=response) as patch_syn_get:
        replies = challengeutils.discussion.get_thread_replies(syn, 222)
        patch_syn_get.assert_called_once_with(
            '/thread/{threadid}/replies?filter={query_filter}'.format(
                threadid=222, query_filter="EXCLUDE_DELETED"),
            limit=20, offset=0)
        # Although actual return isn't a string, this test just makes sure that
        # that the result from _GET_Paginated is returned
        assert replies == response


def test__get_text():
    uri = "myurihere"
    response = "response"
    text_url = {'messageUrl': 'foo?wowthisworks'}
    with mock.patch.object(syn, "restGET",
                           return_value=text_url) as patch_synrestget,\
            mock.patch.object(requests, "get",
                              return_value=response) as patch_requestget:
        text = challengeutils.discussion._get_text(syn, uri)
        patch_synrestget.assert_called_once_with(uri)
        patch_requestget.assert_called_once_with("foo")
        # Although actual return isn't a string, this test just makes sure that
        # that the result from request.get is returned
        assert text == response


def test_get_thread_text():
    messagekey = THREAD_OBJ['messageKey']
    with mock.patch.object(challengeutils.discussion,
                           "_get_text",
                           return_value=TEXT_RESPONSE_MOCK) as patch_get_text:
        thread_text = challengeutils.discussion.get_thread_text(syn, messagekey)
        uri = "/thread/messageUrl?messageKey={key}".format(key=messagekey)
        assert thread_text == 'text'
        patch_get_text.assert_called_once_with(syn, uri)


def test_get_thread_reply_text():
    messagekey = REPLY_OBJ['messageKey']
    with mock.patch.object(challengeutils.discussion,
                           "_get_text",
                           return_value=TEXT_RESPONSE_MOCK) as patch_get_text:
        thread_text = challengeutils.discussion.get_thread_reply_text(syn, messagekey)
        uri = "/reply/messageUrl?messageKey={key}".format(key=messagekey)
        assert thread_text == 'text'
        patch_get_text.assert_called_once_with(syn, uri)


def test_get_forum_participants():
    threads = [THREAD_OBJ]
    profile = synapseclient.UserProfile(ownerId="test")
    with mock.patch.object(challengeutils.discussion,
                           "get_forum_threads",
                           return_value=threads) as patch_get_threads,\
        mock.patch.object(syn,
                          "getUserProfile",
                          return_value=profile) as patch_getuserprofile:
        participants = challengeutils.discussion.get_forum_participants(syn, PROJECTID)
        patch_get_threads.assert_called_once_with(syn, PROJECTID)
        patch_getuserprofile.assert_called_once_with('2222')
        assert participants == [profile]


def test_create_thread():
    title = "my title here"
    message = "my message here"
    discussion_thread_dict = {
        'forumId': FORUM_OBJ['id'],
        'title': title,
        'messageMarkdown': message}
    with mock.patch.object(challengeutils.discussion,
                           "_get_forum_obj",
                           return_value=FORUM_OBJ) as patch_get_obj,\
        mock.patch.object(syn, "restPOST",
                          return_value=THREAD_OBJ) as patch_restpost:
        threadobj = challengeutils.discussion.create_thread(
            syn, PROJECTID, title, message)

        patch_get_obj.assert_called_once_with(syn, PROJECTID)
        patch_restpost.assert_called_once_with(
            '/thread', body=json.dumps(discussion_thread_dict))
        assert threadobj == THREAD_OBJ


def test_create_thread_reply():
    message = "my message here"
    thread_reply_dict = {'threadId': THREAD_OBJ['id'],
                         'messageMarkdown': message}
    with mock.patch.object(syn, "restPOST",
                           return_value=REPLY_OBJ) as patch_get_obj:
        replyobj = challengeutils.discussion.create_thread_reply(
            syn, THREAD_OBJ['id'], message)
        patch_get_obj.assert_called_once_with(
            '/reply', body=json.dumps(thread_reply_dict))
        assert replyobj == REPLY_OBJ
