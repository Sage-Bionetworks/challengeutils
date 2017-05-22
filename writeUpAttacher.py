import synapseclient
import urllib
import argparse

syn = synapseclient.login()

class Query(object):
    """
    An object that helps with paging through annotation query results.

    Also exposes properties totalNumberOfResults, headers and rows.
    """
    def __init__(self, query, limit=20, offset=0):
        self.query = query
        self.limit = limit
        self.offset = offset
        self.fetch_batch_of_results()

    def fetch_batch_of_results(self):
        uri = "/evaluation/submission/query?query=" + urllib.quote_plus("%s limit %s offset %s" % (self.query, self.limit, self.offset))
        results = syn.restGET(uri)
        self.totalNumberOfResults = results['totalNumberOfResults']
        self.headers = results['headers']
        self.rows = results['rows']
        self.i = 0

    def __iter__(self):
        return self

    def next(self):
        if self.i >= len(self.rows):
            if self.offset >= self.totalNumberOfResults:
                raise StopIteration()
            self.fetch_batch_of_results()
        values = self.rows[self.i]['values']
        self.i += 1
        self.offset += 1
        return values

def update_single_submission_status(status, add_annotations, force=False):
    """
    This will update a single submission's status
    :param:    Submission status: syn.getSubmissionStatus()

    :param:    Annotations that you want to add in dict or submission status annotations format.
               If dict, all submissions will be added as private submissions
    """
    existingAnnotations = status.get("annotations", dict())
    privateAnnotations = {each['key']:each['value'] for annots in existingAnnotations for each in existingAnnotations[annots] if annots not in ['scopeId','objectId'] and each['isPrivate'] == True}
    publicAnnotations = {each['key']:each['value'] for annots in existingAnnotations for each in existingAnnotations[annots] if annots not in ['scopeId','objectId'] and each['isPrivate'] == False}

    if not synapseclient.annotations.is_submission_status_annotations(add_annotations):
        privateAddedAnnotations = add_annotations
        publicAddedAnnotations = dict()
    else:
        privateAddedAnnotations = {each['key']:each['value'] for annots in add_annotations for each in add_annotations[annots] if annots not in ['scopeId','objectId'] and each['isPrivate'] == True}
        publicAddedAnnotations = {each['key']:each['value'] for annots in add_annotations for each in add_annotations[annots] if annots not in ['scopeId','objectId'] and each['isPrivate'] == False} 
    #If you add a private annotation that appears in the public annotation, it switches 
    if sum([key in publicAddedAnnotations for key in privateAnnotations]) == 0:
        pass
    elif sum([key in publicAddedAnnotations for key in privateAnnotations]) >0 and force:
        privateAnnotations = {key:privateAnnotations[key] for key in privateAnnotations if key not in publicAddedAnnotations}
    else:
        raise ValueError("You are trying to add public annotations that are already part of the existing private annotations: %s.  Either change the annotation key or specify force=True" % ", ".join([key for key in privateAnnotations if key in publicAddedAnnotations]))
    if sum([key in privateAddedAnnotations for key in publicAnnotations]) == 0:
        pass
    elif sum([key in privateAddedAnnotations for key in publicAnnotations])>0 and force:
        publicAnnotations= {key:publicAnnotations[key] for key in publicAnnotations if key not in privateAddedAnnotations}
    else:
        raise ValueError("You are trying to add private annotations that are already part of the existing public annotations: %s.  Either change the annotation key or specify force=True" % ", ".join([key for key in publicAnnotations if key in privateAddedAnnotations]))

    privateAnnotations.update(privateAddedAnnotations)
    publicAnnotations.update(publicAddedAnnotations)

    priv = synapseclient.annotations.to_submission_status_annotations(privateAnnotations, is_private=True)
    pub = synapseclient.annotations.to_submission_status_annotations(publicAnnotations, is_private=False)

    for annotType in ['stringAnnos', 'longAnnos', 'doubleAnnos']:
        if priv.get(annotType) is not None and pub.get(annotType) is not None:
            if pub.get(annotType) is not None:
                priv[annotType].extend(pub[annotType])
            else:
                priv[annotType] = pub[annotType]
        elif priv.get(annotType) is None and pub.get(annotType) is not None:
            priv[annotType] = pub[annotType]

    status.annotations = priv
    return(status)

def main(writeUpEvalQueue, challengeQueue):
	chal = syn.getSubmissionBundles(challengeQueue, status = "SCORED")

	for sub, stat in chal:
		adding = {}
		team = filter(lambda x: x.get("key") == "team", stat.annotations['stringAnnos'])[0]['value']
		if team.startswith("Yuanfang"):
			allWrite = syn.getSubmissionBundles(writeUpEvalQueue, status = "VALIDATED")
			for subm, writeStat in allWrite:
				subteam = filter(lambda x: x.get("key") == "team", writeStat.annotations['stringAnnos'])[0]['value']
				if subteam == team:
					archived = filter(lambda x: x.get("key") == "archived",writeStat.annotations['stringAnnos'])[0]['value']
					adding = {'writeUp':subm.entityId,'archivedWriteUp':archived}
		else:
			writeups = Query('select entityId, team, status, archived from evaluation_%s where status == "VALIDATED" and team == "%s"' % (writeUpEvalQueue,team.encode('utf-8')))
			if writeups.totalNumberOfResults > 0:
				for i in writeups:
					lastLine = i
				adding = {'writeUp':lastLine[0],'archivedWriteUp':lastLine[3]}
		if len(adding) > 0:
			print("STORING %s writeup" % team)
			add_annots = synapseclient.annotations.to_submission_status_annotations(adding, is_private = False)
			newStatus = update_single_submission_status(stat, add_annots)
			syn.store(newStatus)
		else:
			print("NO WRITEUP: " + team)

def perform_main(args):
    main(args.writeUpQueue, args.chalQueue)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Attach writeup and archived writeups to challenge queue annotations')
    parser.add_argument("writeUpQueue", type=str, help='Write up submission queue evaluation id')
    parser.add_argument("chalQueue", type=str, help='Challenge queue evaluation id')
    args = parser.parse_args()
    perform_main(args)


