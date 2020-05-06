'''
Interact with Synapse discussion API endpoints.
'''
import json
import requests

import synapseclient
from synapseclient.core.utils import id_of

from .synapseservices.discussion import Forum

QUERY_LIMIT = 1000


class DiscussionApi:
    """Discussion API calls"""
    def __init__(self, syn=None):
        if syn is None:
            syn = synapseclient.login()
        self.syn = syn

    def get_project_forum(self, projectid):
        """Get the Forum's metadata for a given project ID.
        https://rest-docs.synapse.org/rest/GET/project/projectId/forum.html
        """
        return Forum(**self.syn.restGET(f'/project/{projectid}/forum'))

    def get_forum(self, forumid):
        """Get the Forum's metadata for a given forum ID.
        https://rest-docs.synapse.org/rest/GET/forum/forumId.html
        """
        return Forum(**self.syn.restGET(f'/forum/{forumid}'))

    def get_forum_threads(self, forumid, query_filter='EXCLUDE_DELETED',
                          limit=20, offset=0):
        """Get N number of threads for a given forum ID
        https://rest-docs.synapse.org/rest/GET/forum/forumId/threads.html

        Args:

            forumid: Forum ID
            query_filter:  filter forum threads returned. Can be NO_FILTER,
                        DELETED_ONLY, EXCLUDE_DELETED.
                        Defaults to EXCLUDE_DELETED.

        Yields:
            list: Forum threads
        """
        uri = f'/forum/{forumid}/threads?filter={query_filter}'
        return self.syn._GET_paginated(uri, limit=limit, offset=offset)

    def post_thread(self, forumid, title, message):
        """Create a new thread in a forum
        https://rest-docs.synapse.org/rest/POST/thread.html

        Args:
            forumid: Forum ID
            title: Title of thread
            message: Content of thread

        Returns:
            DiscussionThreadBundle
        """
        request_obj = {'forumId': forumid,
                       'title': title,
                       'messageMarkdown': message}
        return self.syn.restPOST('/thread',
                                 body=json.dumps(request_obj))

    def get_threads_referencing_entity(self, entityid, limit=20, offset=0):
        """
        Get N number of threads that belongs to projects user can
        view and references the given entity
        https://rest-docs.synapse.org/rest/GET/entity/id/threads.html

        Args:
            syn: Synapse object
            entityid: Synapse Entity id

        Yields:
            DiscussionThreadBundles
        """
        return self.syn._GET_paginated(f"/entity/{entityid}/threads",
                                       limit=limit, offset=offset)

    def get_thread(self, threadid):
        """Get a thread and its statistic given its ID
        https://rest-docs.synapse.org/rest/GET/thread/threadId.html
        """
        return self.syn.restGET(f"/thread/{threadid}")

    def update_thread_title(self, threadid):
        """Update title of a thread
        https://rest-docs.synapse.org/rest/PUT/thread/threadId/title.html
        """
        return self.syn.restPOST(f"/thread/{threadid}/title")

    def update_thread_message(self, threadid):
        """Update message of a thread
        https://rest-docs.synapse.org/rest/PUT/thread/threadId/message.html
        """
        return self.syn.restPOST(f"/thread/{threadid}/message")

    def delete_thread(self, threadid):
        """Delete thread
        https://rest-docs.synapse.org/rest/DELETE/thread/threadId.html
        """
        return self.syn.restDELETE(f"/thread/{threadid}")

    def restore_thread(self, threadid):
        """Restore a deleted thread
        https://rest-docs.synapse.org/rest/PUT/thread/threadId/restore.html
        """
        return self.syn.restPUT(f"/thread/{threadid}/restore")

    def pin_thread(self, threadid):
        """Pin a thread
        https://rest-docs.synapse.org/rest/PUT/thread/threadId/pin.html
        """
        return self.syn.restPUT(f"/thread/{threadid}/pin")

    def unpin_thread(self, threadid):
        """Unpin a thread
        https://rest-docs.synapse.org/rest/PUT/thread/threadId/unpin.html
        """
        return self.syn.restPUT(f"/thread/{threadid}/unpin")

    def get_thread_message_url(self, messagekey):
        """message URL of a thread. The message URL is the URL
        to download the file which contains the thread message.
        https://rest-docs.synapse.org/rest/GET/thread/messageUrl.html
        """
        return self.syn.restGET(f"/thread/messageUrl?messageKey={messagekey}")

    def post_reply(self, threadid, message):
        """Create a new thread in a forum
        https://rest-docs.synapse.org/rest/POST/reply.html

        Args:
            threadid: Thread ID
            message: Content of reply

        Returns:
            DiscussionReplyBundle
        """
        create_reply = {'threadId': threadid, 'messageMarkdown': message}
        return self.syn.restPOST('/reply', body=json.dumps(create_reply))

    def get_reply(self, replyid):
        """Get a reply"""
        return self.syn.restGET(f'/reply/{replyid}')

    def get_thread_replies(self, threadid, query_filter='EXCLUDE_DELETED',
                           limit=20, offset=0):
        """Get N number of replies for a given thread ID
        https://rest-docs.synapse.org/rest/GET/thread/threadId/replies.html

        Args:
            threadid: Forum thread id
            query_filter:  filter forum thread replies returned.
                           Can be NO_FILTER, DELETED_ONLY, EXCLUDE_DELETED.
                           Defaults to EXCLUDE_DELETED.
        Yields:
            list: Forum threads replies
        """
        replies = f'/thread/{threadid}/replies?filter={query_filter}'
        return self.syn._GET_paginated(replies, limit=limit, offset=offset)

    def get_reply_message_url(self, messagekey):
        """message URL of a thread. The message URL is the URL
        to download the file which contains the thread message.
        https://rest-docs.synapse.org/rest/GET/reply/messageUrl.html
        """
        return self.syn.restGET(f"/reply/messageUrl?messageKey={messagekey}")

    def get_forum_threadcount(self, forumid, query_filter='EXCLUDE_DELETED'):
        """Total number of threads given forum ID
        https://rest-docs.synapse.org/rest/GET/forum/forumId/threadcount.html
        """
        threadcount = f'/forum/{forumid}/threadcount?filter={query_filter}'
        return self.syn.restGET(threadcount)

    def get_thread_replycount(self, threadid, query_filter='EXCLUDE_DELETED'):
        """Total number of replies given thread ID
        https://rest-docs.synapse.org/rest/GET/thread/threadId/replycount.html
        """
        replycount = f'/thread/{threadid}/replycount?filter={query_filter}'
        return self.syn.restGET(replycount)

    def get_forum_moderators(self, forumid):
        """Get moderators given a forum ID
        https://rest-docs.synapse.org/rest/GET/forum/forumId/moderators.html
        """
        return self.syn._GET_paginated(f'/forum/{forumid}/moderators')

    def get_threadcount_referencing_entities(self, entityid_list):
        """Get list of entity and count pairs, with count is the number of
        threads that belongs to projects user can view and references
        the given entity.
        https://rest-docs.synapse.org/rest/POST/entity/threadcounts.html
        """
        entities = {'idList': entityid_list}
        return self.syn.restPOST('/entity/threadcounts',
                                 body=json.dumps(entities))


def get_forum_threads(syn, ent, query_filter='EXCLUDE_DELETED',
                      limit=20, offset=0):
    """
    Gets threads from a forum

    Args:
        syn: synapse object
        ent: Synapse Project entity or id
        query_filter:  filter forum threads returned. Can be NO_FILTER,
                       DELETED_ONLY, EXCLUDE_DELETED.
                       Defaults to EXCLUDE_DELETED.

    Yields:
        list: Forum threads
    """
    api = DiscussionApi(syn)
    synid = id_of(ent)
    forum_obj = api.get_project_forum(synid)
    response = api.get_forum_threads(forum_obj.id,
                                     query_filter=query_filter,
                                     limit=limit, offset=offset)
    return response


def get_thread_replies(syn, thread, query_filter='EXCLUDE_DELETED',
                       limit=20, offset=0):
    """Gets replies of a thread

    Args:
        syn: synapse object
        thread: Synapse thread or id
        query_filter:  filter forum threads returned. Can be NO_FILTER,
                       DELETED_ONLY, EXCLUDE_DELETED.
                       Defaults to EXCLUDE_DELETED.

    Yields:
        list: Thread replies
    """
    api = DiscussionApi(syn)
    threadid = id_of(thread)
    response = api.get_thread_replies(threadid,
                                      query_filter=query_filter,
                                      limit=limit, offset=offset)
    return response


def _get_text(url):
    '''
    Get the text from a message url

    Args:
        url: rest call URL

    Returns:
        response: Request response
    '''
    response = requests.get(url['messageUrl'].split("?")[0])
    return response


def get_thread_text(syn, messagekey):
    '''
    Get thread text by the messageKey that is returned by getting thread

    Args:
        syn: Synapse object
        messagekey: Three part key from DiscussionThreadBundle.messageKey

    Returns:
        str: Thread text
    '''
    api = DiscussionApi(syn)
    url = api.get_thread_message_url(messagekey)
    thread_response = _get_text(url)
    return thread_response.text


def get_thread_reply_text(syn, messagekey):
    '''
    Get thread reply text by the messageKey that is returned by
    getting thread replies

    Args:
        syn: Synapse object
        messagekey: Four part key from DiscussionReplyBundle.messageKey

    Returns:
        str: Thread text
    '''
    api = DiscussionApi(syn)
    url = api.get_reply_message_url(messagekey)
    thread_reply_response = _get_text(url)
    return thread_reply_response.text


def get_forum_participants(syn, ent):
    '''
    Get all forum participants

    Args:
        ent: Synapse Project entity or id
        synid: Synapse Project id

    Return:
        list: user profiles active in forum
    '''
    synid = id_of(ent)
    threads = get_forum_threads(syn, synid)
    users = set()
    for thread in threads:
        unique_users = set(thread['activeAuthors'])
        users.update(unique_users)
    userprofiles = [syn.getUserProfile(user) for user in users]
    return userprofiles


def create_thread(syn, ent, title, message):
    '''
    Create a thread

    Args:
        syn: synapse object
        ent: Synapse Project entity or id
        title: title of thread
        message: message in thread

    Returns:
        dict: Thread bundle
    '''
    api = DiscussionApi(syn)
    synid = id_of(ent)
    forum_obj = api.get_project_forum(synid)
    thread_obj = api.post_thread(forum_obj.id, title, message)
    return thread_obj


def create_thread_reply(syn, threadid, message):
    """Creates a reply to a thread

    Args:
        syn: synapse object
        threadid: Synapse Thread id
        message: message in reply

    Returns:
        dict: Reply bundle
    """
    api = DiscussionApi(syn)
    replyobj = api.post_reply(threadid, message)
    return replyobj


def copy_thread(syn, thread, project):
    """Copies a discussion thread to a project

    Args:
        syn: synapse object
        thread: Synapse Thread
        project: Synapse Project or its id to copy thread to

    Returns:
        dict: Thread bundle
    """
    projectid = id_of(project)
    title = thread['title']
    author = thread['createdBy']
    username = syn.getUserProfile(author)['userName']
    on_behalf_of = "On behalf of @{user}\n\n".format(user=username)
    text = get_thread_text(syn, thread['messageKey'])
    new_thread_text = on_behalf_of + text

    return create_thread(syn, projectid, title, new_thread_text)


def copy_reply(syn, reply, thread):
    """Copies a discussion thread reply to a thread

    Args:
        syn: synapse object
        reply: Synapse Reply
        thread: Synapse thread or threadid to copy reply to

    Returns:
        dict: Reply bundle
    """
    threadid = id_of(thread)
    author = reply['createdBy']
    username = syn.getUserProfile(author)['userName']
    on_behalf_of = "On behalf of @{user}\n\n".format(user=username)
    text = get_thread_reply_text(syn, reply['messageKey'])
    new_reply_text = on_behalf_of + text
    return create_thread_reply(syn, threadid, new_reply_text)


def copy_forum(syn, project, new_project):
    """Copies the discussion forum of a project to another project

    Args:
        syn: synapse object
        project: Synapse Project
        new_project: Synapse Project to copy forum to
    """
    threads = get_forum_threads(syn, project)
    for thread in threads:
        new_thread_obj = copy_thread(syn, thread, new_project)
        thread_replies = get_thread_replies(syn, thread['id'])
        for reply in thread_replies:
            copy_reply(syn, reply, new_thread_obj['id'])
