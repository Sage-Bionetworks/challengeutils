'''
Interact with Synapse discussion API endpoints.
'''
import json
from typing import Iterator, List, Union

import requests
import synapseclient
from synapseclient import Project, Synapse, UserProfile
from synapseclient.core.utils import id_of

from .synapseservices.discussion import Forum, Thread, Reply

QUERY_LIMIT = 1000


class DiscussionApi:
    """Discussion API calls"""
    def __init__(self, syn: Synapse = None):
        if syn is None:
            syn = synapseclient.login()
        self.syn = syn

    def get_project_forum(self, projectid: str) -> Forum:
        """Get the Forum's metadata for a given project ID.
        https://rest-docs.synapse.org/rest/GET/project/projectId/forum.html
        """
        return Forum(**self.syn.restGET(f'/project/{projectid}/forum'))

    def get_forum(self, forumid: str) -> Forum:
        """Get the Forum's metadata for a given forum ID.
        https://rest-docs.synapse.org/rest/GET/forum/forumId.html
        """
        return Forum(**self.syn.restGET(f'/forum/{forumid}'))

    def get_forum_threads(self, forumid: str,
                          query_filter: str = 'EXCLUDE_DELETED',
                          **kwargs) -> Iterator[Thread]:
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
        threads = self.syn._GET_paginated(uri, **kwargs)
        for thread in threads:
            yield Thread(**thread)

    def post_thread(self, forumid: str, title: str, message: str) -> Thread:
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
        thread = self.syn.restPOST('/thread',
                                   body=json.dumps(request_obj))
        return Thread(**thread)

    def get_threads_referencing_entity(self, entityid: str,
                                       **kwargs) -> Iterator[Thread]:
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
        threads = self.syn._GET_paginated(f"/entity/{entityid}/threads",
                                          **kwargs)
        for thread in threads:
            yield Thread(**thread)

    def get_thread(self, threadid: str) -> Thread:
        """Get a thread and its statistic given its ID
        https://rest-docs.synapse.org/rest/GET/thread/threadId.html
        """
        return Thread(**self.syn.restGET(f"/thread/{threadid}"))

    def update_thread_title(self, threadid: str) -> Thread:
        """Update title of a thread
        https://rest-docs.synapse.org/rest/PUT/thread/threadId/title.html
        """
        return Thread(**self.syn.restPUT(f"/thread/{threadid}/title"))

    def update_thread_message(self, threadid: str) -> Thread:
        """Update message of a thread
        https://rest-docs.synapse.org/rest/PUT/thread/threadId/message.html
        """
        return Thread(**self.syn.restPUT(f"/thread/{threadid}/message"))

    def delete_thread(self, threadid: str):
        """Delete thread
        https://rest-docs.synapse.org/rest/DELETE/thread/threadId.html
        """
        self.syn.restDELETE(f"/thread/{threadid}")

    def restore_thread(self, threadid: str):
        """Restore a deleted thread
        https://rest-docs.synapse.org/rest/PUT/thread/threadId/restore.html
        """
        self.syn.restPUT(f"/thread/{threadid}/restore")

    def pin_thread(self, threadid: str):
        """Pin a thread
        https://rest-docs.synapse.org/rest/PUT/thread/threadId/pin.html
        """
        self.syn.restPUT(f"/thread/{threadid}/pin")

    def unpin_thread(self, threadid: str):
        """Unpin a thread
        https://rest-docs.synapse.org/rest/PUT/thread/threadId/unpin.html
        """
        self.syn.restPUT(f"/thread/{threadid}/unpin")

    def get_thread_message_url(self, messagekey: str) -> dict:
        """message URL of a thread. The message URL is the URL
        to download the file which contains the thread message.
        https://rest-docs.synapse.org/rest/GET/thread/messageUrl.html
        """
        return self.syn.restGET(f"/thread/messageUrl?messageKey={messagekey}")

    def post_reply(self, threadid: str, message: str) -> Reply:
        """Create a new thread in a forum
        https://rest-docs.synapse.org/rest/POST/reply.html

        Args:
            threadid: Thread ID
            message: Content of reply

        Returns:
            DiscussionReplyBundle
        """
        create_reply = {'threadId': threadid, 'messageMarkdown': message}
        return Reply(**self.syn.restPOST('/reply',
                                         body=json.dumps(create_reply)))

    def get_reply(self, replyid: str) -> Reply:
        """Get a reply
        https://rest-docs.synapse.org/rest/GET/reply/replyId.html"""
        return Reply(**self.syn.restGET(f'/reply/{replyid}'))

    def get_thread_replies(self, threadid: str,
                           query_filter: str = 'EXCLUDE_DELETED',
                           **kwargs):
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
        replies = self.syn._GET_paginated(
            f'/thread/{threadid}/replies?filter={query_filter}',
            **kwargs
        )
        for reply in replies:
            yield Reply(**reply)

    def get_reply_message_url(self, messagekey: str) -> dict:
        """message URL of a thread. The message URL is the URL
        to download the file which contains the thread message.
        https://rest-docs.synapse.org/rest/GET/reply/messageUrl.html
        """
        return self.syn.restGET(f"/reply/messageUrl?messageKey={messagekey}")

    def get_forum_threadcount(self, forumid: str,
                              query_filter: str = 'EXCLUDE_DELETED') -> int:
        """Total number of threads given forum ID
        https://rest-docs.synapse.org/rest/GET/forum/forumId/threadcount.html
        """
        threadcount = f'/forum/{forumid}/threadcount?filter={query_filter}'
        return self.syn.restGET(threadcount)['count']

    def get_thread_replycount(self, threadid: str,
                              query_filter: str = 'EXCLUDE_DELETED') -> int:
        """Total number of replies given thread ID
        https://rest-docs.synapse.org/rest/GET/thread/threadId/replycount.html
        """
        replycount = f'/thread/{threadid}/replycount?filter={query_filter}'
        return self.syn.restGET(replycount)['count']

    def get_forum_moderators(self, forumid: str) -> Iterator[int]:
        """Get moderators given a forum ID
        https://rest-docs.synapse.org/rest/GET/forum/forumId/moderators.html
        """
        return self.syn._GET_paginated(f'/forum/{forumid}/moderators')

    def get_threadcount_referencing_entities(self,
                                             entityid_list: list) -> list:
        """Get list of entity and count pairs, with count is the number of
        threads that belongs to projects user can view and references
        the given entity.
        https://rest-docs.synapse.org/rest/POST/entity/threadcounts.html
        """
        entities = {'idList': entityid_list}
        return self.syn.restPOST('/entity/threadcounts',
                                 body=json.dumps(entities))


def get_forum_threads(syn: Synapse, ent: Union[Project, str],
                      **kwargs) -> Iterator[Thread]:
    """
    Gets threads from a forum

    Args:
        syn: synapse object
        ent: Synapse Project entity or id
        **kwargs: query_filter - filter forum threads returned. Can be,
                  NO_FILTER, DELETED_ONLY, EXCLUDE_DELETED.
                  Defaults to EXCLUDE_DELETED.
                  limit - Number of query results
                  offset -  Page of query result

    Yields:
        synapseservices.Thread

    """
    api = DiscussionApi(syn)
    synid = id_of(ent)
    forum_obj = api.get_project_forum(synid)
    threads = api.get_forum_threads(forum_obj.id, **kwargs)
    return threads


def get_thread_replies(syn: Synapse, thread: Thread,
                       **kwargs) -> Iterator[Reply]:
    """Gets replies of a thread

    Args:
        syn: synapse object
        thread: Synapse thread or id
        **kwargs: query_filter: filter forum threads returned. Can be,
                  NO_FILTER, DELETED_ONLY, EXCLUDE_DELETED.
                  Defaults to EXCLUDE_DELETED.
                  limit - Number of query results
                  offset -  Page of query result

    Yields:
        synapseservices.Reply

    """
    api = DiscussionApi(syn)
    threadid = id_of(thread)
    replies = api.get_thread_replies(threadid, **kwargs)
    return replies


def _get_text(url: str):
    '''
    Get the text from a message url

    Args:
        url: rest call URL

    Returns:
        response: Request response
    '''
    response = requests.get(url['messageUrl'].split("?")[0])
    return response


def get_thread_text(syn: Synapse, thread: Union[Thread, str]) -> str:
    '''
    Get a thread's text

    Args:
        syn: Synapse object
        thread: challengeutils.synapseservices.Thread or its id

    Returns:
        str: Thread text
    '''
    api = DiscussionApi(syn)
    if not isinstance(thread, Thread):
        thread = api.get_thread(thread)
    # Get the message URL with the message key
    url = api.get_thread_message_url(thread.messagekey)
    thread_response = _get_text(url)
    return thread_response.text


def get_thread_reply_text(syn, reply: Reply) -> str:
    '''
    Get thread reply text

    Args:
        syn: Synapse object
        messagekey: Four part key from DiscussionReplyBundle.messageKey

    Returns:
        str: Thread text
    '''
    api = DiscussionApi(syn)
    if not isinstance(reply, Reply):
        reply = api.get_reply(reply)
    url = api.get_reply_message_url(reply.messagekey)
    thread_reply_response = _get_text(url)
    return thread_reply_response.text


def get_forum_participants(syn: Synapse,
                           ent: Union[Project, str]) -> List[UserProfile]:
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
        unique_users = set(thread.active_authors)
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


def copy_thread(syn: Synapse, thread: Thread,
                project: Union[Project, str]) -> Thread:
    """Copies a discussion thread and its replies to a project

    Args:
        syn: synapse object
        thread: Synapse Thread
        project: Synapse Project or its id to copy thread to

    Returns:
        dict: Thread bundle
    """
    new_thread_obj = _copy_thread(syn, thread, project)
    thread_replies = get_thread_replies(syn, thread.id)
    for reply in thread_replies:
        copy_reply(syn, reply, new_thread_obj.id)
    return new_thread_obj


def _copy_thread(syn, thread: Thread, project: Union[Project, str]) -> Thread:
    """Copies a discussion thread to a project

    Args:
        syn: synapse object
        thread: Synapse Thread
        project: Synapse Project or its id to copy thread to

    Returns:
        synapseservices.Thread
    """
    projectid = id_of(project)
    title = thread.title
    author = thread.createdby
    username = syn.getUserProfile(author)['userName']
    on_behalf_of = f"On behalf of @{username}\n\n"
    text = get_thread_text(syn, thread)
    new_thread_text = on_behalf_of + text
    new_thread_obj = create_thread(syn, projectid, title, new_thread_text)

    return new_thread_obj


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
    author = reply.createdby
    username = syn.getUserProfile(author)['userName']
    on_behalf_of = "On behalf of @{user}\n\n".format(user=username)
    text = get_thread_reply_text(syn, reply)
    new_reply_text = on_behalf_of + text
    return create_thread_reply(syn, threadid, new_reply_text)


def copy_forum(syn: Synapse, project: Union[Project, str],
               new_project: Union[Project, str]):
    """Copies the discussion forum of a project to another project

    Args:
        syn: synapse object
        project: Synapse Project or its id
        new_project: Synapse Project to copy forum to
    """
    threads = get_forum_threads(syn, project)
    for thread in threads:
        copy_thread(syn, thread, new_project)
