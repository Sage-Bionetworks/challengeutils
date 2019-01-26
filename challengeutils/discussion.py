import synapseclient
import os
from synapseclient.exceptions import *
import json
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
    forum_obj =syn.restGET('/project/{projectid}/forum'.format(projectid=synid))
    return(forum_obj)

def get_forum_threads(syn, synid, query_filter='EXCLUDE_DELETED'):
    """
    Get threads from a forum

    Args:
        syn: synapse object
        synid: Synapse Project id
        query_filter:  filter forum threads returned. Can be NO_FILTER, DELETED_ONLY, EXCLUDE_DELETED.  Defaults to EXCLUDE_DELETED.
    
    Yields:
        json: Forum threads
    """
    forum_obj = _get_forum_obj(syn, synid)
    forumid = forum_obj['id']

    #total_results = syn.restGET('/forum/{forumid}/threads?limit=20&offset=0&filter=EXCLUDE_DELETED'.format(forumid=forumid))['totalNumberOfResults']

    #options = {'limit':20, 'offset':0}
    limit = 20
    offset = 0

    while True:
        #remaining = options['limit'] + options['offset'] - offset

        # Handle the case where a query was skipped due to size and now no items remain
        #if remaining <= 0:
        #    raise(StopIteration)

        try:
            response = syn.restGET('/forum/{forumid}/threads?limit={limit}&offset={offset}&filter={query_filter}'.format(forumid=forumid, limit=limit, offset=offset, query_filter=query_filter))
            for res in response['results']:
                yield res
                
            #Exit when no more results can be pulled
            if len(response['results']) > 0:
                offset += limit
            else:
                break

        except SynapseHTTPError as err:
            # Shrink the query size when appropriate
            if err.response.status_code == 400 and ('The results of this query exceeded the max' in err.response.json()['reason']):
                if (limit == 1):
                    sys.stderr.write("A single row (offset %s) of this query "
                                     "exceeds the maximum size.  Consider "
                                     "limiting the columns returned "
                                     "in the select clause.  Skipping...\n" % offset)
                    offset += 1
                    # Since these large rows are anomalous, reset the limit
                    limit = QUERY_LIMIT
                else:
                    limit = limit // 2
            else:
                raise

def get_thread_replies(syn, threadid, query_filter='EXCLUDE_DELETED'):
    """
    Get threads from a forum

    Args:
        syn: synapse object
        threadid: Forum thread id
        query_filter:  filter forum thread replies returned. Can be NO_FILTER, DELETED_ONLY, EXCLUDE_DELETED.  Defaults to EXCLUDE_DELETED.
    
    Yields:
        json: Forum threads
    """

    #totalResults = syn.restGET('/thread/%s/replies?limit=20&offset=0&filter=EXCLUDE_DELETED' % threadId)['totalNumberOfResults']

    #options = {'limit':20, 'offset':0}
    limit = 20
    offset = 0

    while True:
        # remaining = options['limit'] + options['offset'] - offset

        # # Handle the case where a query was skipped due to size and now no items remain
        # if remaining <= 0:
        #     raise(StopIteration)

        try:
            response = syn.restGET('/thread/{threadid}/replies?limit={limit}&offset={offset}&filter={query_filter}'.format(threadid=threadid, limit=limit, offset=offset, query_filter=query_filter))
            for res in response['results']:
                yield res

            # Exit when no more results can be pulled
            if len(response['results']) > 0:
                offset += limit
            else:
                break

            # Exit when all requests results have been pulled
            #if offset > options['offset'] + options['limit'] - 1:
             #   break
        except SynapseHTTPError as err:
            # Shrink the query size when appropriate
            if err.response.status_code == 400 and ('The results of this query exceeded the max' in err.response.json()['reason']):
                if (limit == 1):
                    sys.stderr.write("A single row (offset %s) of this query "
                                     "exceeds the maximum size.  Consider "
                                     "limiting the columns returned "
                                     "in the select clause.  Skipping...\n" % offset)
                    offset += 1
                    # Since these large rows are anomalous, reset the limit
                    limit = QUERY_LIMIT
                else:
                    limit = limit // 2
            else:
                raise


def get_thread_text(messagekey):
    '''
    Get thread text by the messageKey that is returned by getting thread
   
    Args:
        messagekey: Three part key from DiscussionThreadBundle.messageKey

    Returns:
        str: Thread text
    '''

    thread_text = requests.get("https://s3.amazonaws.com/prod.discussion.sagebase.org/{url}".format(url=messagekey),timeout=3)
    return(thread_text.text)


def get_thread_reply_text(messagekey):
    '''
    Get thread reply text by the messageKey that is returned by getting thread replies
   
    Args:
        messagekey: Three part key from DiscussionReplyBundle.messageKey

    Returns:
        str: Thread text
    '''

    thread_reply_text = requests.get("https://s3.amazonaws.com/prod.discussion.sagebase.org/{url}".format(url=messagekey),timeout=3)
    return(thread_reply_text.text)

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
        users.add(thread['activeAuthors'])
    userprofiles = [syn.getUserProfile(user) for user in users]
    return(userprofiles)

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
    discussion_thread_dict = {'forumId':forumid, 'title':title, 'messageMarkdown':message}
    thread_obj = syn.restPOST('/thread',body=json.dumps(discussion_thread_dict))
    return(thread_obj)

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
    thread_reply_dict = {'threadId':threadid, 'messageMarkdown':message}
    reply_obj = syn.restPOST('/reply',body=json.dumps(thread_reply_dict))
    return(reply_obj)
