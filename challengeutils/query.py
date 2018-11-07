import urllib
import sys

def evaluation_queue_query(syn, uri, limit=20, offset=0):
    """
    :param syn:     A Synapse object
    :param uri:     A URI for evaluation queues (select * from evaluation_12345)
    :param limit:   How many records should be returned per request
    :param offset:  At what record offset from the first should iteration start

    :returns: A generator over some paginated results

    The limit parameter is set at 20 by default. Using a larger limit results in fewer calls to the service, but if
    responses are large enough to be a burden on the service they may be truncated.
    """

    prev_num_results = sys.maxsize
    while prev_num_results > 0:
        rest_uri = "/evaluation/submission/query?query=" + urllib.parse.quote_plus("%s limit %s offset %s" % (uri, limit, offset))
        page = syn.restGET(rest_uri)
        #results = page['results'] if 'results' in page else page['children']
        results = [{page['headers'][index]:value  for index, value in enumerate(row['values']) } for row in page['rows'] ]
        prev_num_results = len(results)
        for result in results:
            offset += 1
            yield result