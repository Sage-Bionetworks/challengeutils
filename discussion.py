import synapseclient
import os
from synapseclient.exceptions import *

QUERY_LIMIT = 1000


def _getForumId(syn, synId):
    return(syn.restGET('/project/%s/forum' % synId)['id'])


def getForumThreads(syn, synId):
    """
    Filter = NO_FILTER, DELETED_ONLY, EXCLUDE_DELETED
    """
    forumId = _getForumId(syn, synId)

    totalResults = syn.restGET('/forum/%s/threads?limit=20&offset=0&filter=EXCLUDE_DELETED' % forumId)['totalNumberOfResults']

    options = {'limit':20, 'offset':0}
    limit = 20
    offset = 0

    while True:
        #remaining = options['limit'] + options['offset'] - offset

        # Handle the case where a query was skipped due to size and now no items remain
        #if remaining <= 0:
        #    raise(StopIteration)

        try:
            response = syn.restGET('/forum/%s/threads?limit=%d&offset=%d&filter=EXCLUDE_DELETED'%(forumId, limit, offset))
            for res in response['results']:
                yield res
                
            #Exit when no more results can be pulled
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

def getThreadReplies(syn, threadId):
    totalResults = syn.restGET('/thread/%s/replies?limit=20&offset=0&filter=EXCLUDE_DELETED' % threadId)['totalNumberOfResults']

    options = {'limit':20, 'offset':0}
    limit = 20
    offset = 0

    while True:
        remaining = options['limit'] + options['offset'] - offset

        # Handle the case where a query was skipped due to size and now no items remain
        if remaining <= 0:
            raise(StopIteration)

        try:
            response = syn.restGET('/thread/%s/replies?limit=%d&offset=%d&filter=EXCLUDE_DELETED'%(threadId, limit, offset))
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

def getForumParticipants(syn, synId):
    threads = getForumThreads(syn, synId)
    users = []
    for i in threads:
        users.extend(i['activeAuthors'])
    users = set(users)
    userprofiles = [syn.getUserProfile(x) for x in users]
    return(userprofiles)


