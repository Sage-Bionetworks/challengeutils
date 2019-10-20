'''
Functions that interact with the Synapse discussion API
'''
import json
import requests
import synapseclient
QUERY_LIMIT = 1000


def _get_forum_obj(syn, synid):
    '''
    Get forum id

    Args:
        syn: Synapse object
        synid: Synapse Project id

    Returns:
        dict: Forum object
    '''
    uri = '/project/{projectid}/forum'.format(projectid=synid)
    forum_obj = syn.restGET(uri)
    return forum_obj


def get_forum_threads(syn, synid, query_filter='EXCLUDE_DELETED',
                      limit=20, offset=0):
    """
    Get threads from a forum

    Args:
        syn: synapse object
        synid: Synapse Project id
        query_filter:  filter forum threads returned. Can be NO_FILTER,
                       DELETED_ONLY, EXCLUDE_DELETED.
                       Defaults to EXCLUDE_DELETED.

    Yields:
        list: Forum threads
    """
    forum_obj = _get_forum_obj(syn, synid)
    forumid = forum_obj['id']
    uri = '/forum/{forumid}/threads?filter=''{query_filter}'.format(
        forumid=forumid, query_filter=query_filter)
    response = syn._GET_paginated(uri, limit=limit, offset=offset)
    return response


def get_thread_replies(syn, threadid, query_filter='EXCLUDE_DELETED',
                       limit=20, offset=0):
    """
    Get thread replies from a thread

    Args:
        syn: synapse object
        threadid: Forum thread id
        query_filter:  filter forum thread replies returned.
                       Can be NO_FILTER, DELETED_ONLY, EXCLUDE_DELETED.
                       Defaults to EXCLUDE_DELETED.

    Yields:
        list: Forum threads replies
    """
    response = syn._GET_paginated(
        '/thread/{threadid}/replies?filter={query_filter}'.format(
            threadid=threadid, query_filter=query_filter),
        limit=limit, offset=offset)
    return response


def _get_text(syn, uri):
    '''
    Get the text from a message url

    Args:
        syn: Synapse object
        uri: rest call URL

    Returns:
        response: Request response
    '''
    text_url = syn.restGET(uri)
    response = requests.get(text_url['messageUrl'].split("?")[0])
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
    uri = "/thread/messageUrl?messageKey={key}".format(key=messagekey)
    thread_response = _get_text(syn, uri)
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
    uri = "/reply/messageUrl?messageKey={key}".format(key=messagekey)
    thread_reply_response = _get_text(syn, uri)
    return thread_reply_response.text


def get_forum_participants(syn, synid):
    '''
    Get all forum participants

    Args:
        syn: Synapse id
        synid: Synapse Project id

    Return:
        list: user profiles active in forum
    '''
    threads = get_forum_threads(syn, synid)
    users = set()
    for thread in threads:
        unique_users = set(thread['activeAuthors'])
        users.update(unique_users)
    userprofiles = [syn.getUserProfile(user) for user in users]
    return userprofiles


def create_thread(syn, synid, title, message):
    '''
    Create a thread

    Args:
        syn: synapse object
        synid: Synapse Project id
        title: title of thread
        message: message in thread

    Returns:
        dict: Thread bundle
    '''
    forum_obj = _get_forum_obj(syn, synid)
    forumid = forum_obj['id']
    discussion_thread_dict = {'forumId': forumid,
                              'title': title,
                              'messageMarkdown': message}
    thread_obj = syn.restPOST('/thread',
                              body=json.dumps(discussion_thread_dict))
    return thread_obj


def create_thread_reply(syn, threadid, message):
    '''
    Create a thread

    Args:
        syn: synapse object
        threadid: Thread id
        message: message in thread

    Returns:
        dict: Reply bundle
    '''
    thread_reply_dict = {'threadId': threadid, 'messageMarkdown': message}
    reply_obj = syn.restPOST('/reply', body=json.dumps(thread_reply_dict))
    return reply_obj


def get_entity_threads(syn, entityid):
    '''
    Get the discussion threads that the entity has been
    mentioned on

    Args:
        syn: Synapse object
        entityid: Synapse Entity id

    Returns:
        threads
    '''
    uri = "/entity/{entityid}/threads".format(entityid=entityid)
    results = syn._GET_paginated(uri)
    return results


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
        return self.syn.restGET(f'/project/{projectid}/forum')

    def get_forum(self, forumid):
        """Get the Forum's metadata for a given forum ID.
        https://rest-docs.synapse.org/rest/GET/forum/forumId.html
        """
        return self.syn.restGET(f'/forum/{forumid}')

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

        Args:
            syn: Synapse object
            entityid: Synapse Entity id

        Yields:
            DiscussionThreadBundles
        """
        return self.syn._GET_paginated(f"/entity/{entityid}/threads",
                                       limit=limit, offset=offset)

    def get_thread(self, threadid):
        """Get a thread and its statistic given its ID"""
        return self.syn.restGET(f"/thread/{threadid}")
