import synapseclient
import urllib
import sys

def update_single_submission_status(status, add_annotations, to_public=False, force_change_annotation_acl=False):
	"""
	This will update a single submission's status
	
	:param:    Submission status: syn.getSubmissionStatus()
	:param:    Annotations that you want to add in dict or submission status annotations format.
			   If dict, all submissions will be added as private submissions
	"""
	existing_annotations = status.get("annotations", dict())
	private_annotations = {annotation['key']:annotation['value'] for annotation_type in existing_annotations for annotation in existing_annotations[annotation_type] if annotation_type not in ['scopeId','objectId'] and annotation['isPrivate'] == True}
	public_annotations = {annotation['key']:annotation['value'] for annotation_type in existing_annotations for annotation in existing_annotations[annotation_type] if annotation_type not in ['scopeId','objectId'] and annotation['isPrivate'] == False}

	if not synapseclient.annotations.is_submission_status_annotations(add_annotations):
		private_added_annotations =  dict() if to_public else add_annotations
		public_added_annotations = add_annotations if to_public else dict()
	else:
		private_added_annotations = {annotation['key']:annotation['value'] for annotation_type in add_annotations for annotation in existing_annotations[annotation_type] if annotation_type not in ['scopeId','objectId'] and annotation['isPrivate'] == True}
		public_added_annotations = {annotation['key']:annotation['value'] for annotation_type in add_annotations for annotation in existing_annotations[annotation_type] if annotation_type not in ['scopeId','objectId'] and annotation['isPrivate'] == False}
	#If you add a private annotation that appears in the public annotation, it switches 
	if sum([key in public_added_annotations for key in private_annotations]) == 0:
		pass
	elif sum([key in public_added_annotations for key in private_annotations]) >0 and force_change_annotation_acl:
		#Filter out the annotations that have changed ACL
		private_annotations = {key:private_annotations[key] for key in private_annotations if key not in public_added_annotations}
	else:
		raise ValueError("You are trying to change the ACL of these annotation key(s): %s.  Either change the annotation key or specify force_change_annotation_acl=True" % ", ".join([key for key in private_annotations if key in public_added_annotations]))
	if sum([key in private_added_annotations for key in public_annotations]) == 0:
		pass
	elif sum([key in private_added_annotations for key in public_annotations])>0 and force_change_annotation_acl:
		public_annotations= {key:public_annotations[key] for key in public_annotations if key not in private_added_annotations}
	else:
		raise ValueError("You are trying to change the ACL of these annotation key(s): %s.  Either change the annotation key or specify force_change_annotation_acl=True" % ", ".join([key for key in public_annotations if key in private_added_annotations]))
	private_annotations.update(private_added_annotations)
	public_annotations.update(public_added_annotations)

	priv = synapseclient.annotations.to_submission_status_annotations(private_annotations, is_private=True)
	pub = synapseclient.annotations.to_submission_status_annotations(public_annotations, is_private=False)
	#Combined private and public annotations into one
	for annotation_type in ['stringAnnos', 'longAnnos', 'doubleAnnos']:
		if priv.get(annotation_type) is not None and pub.get(annotation_type) is not None:
			if pub.get(annotation_type) is not None:
				priv[annotation_type].extend(pub[annotation_type])
			else:
				priv[annotation_type] = pub[annotation_type]
		elif priv.get(annotation_type) is None and pub.get(annotation_type) is not None:
			priv[annotation_type] = pub[annotation_type]

	status.annotations = priv
	return(status)

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
