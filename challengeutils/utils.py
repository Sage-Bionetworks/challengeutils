import synapseclient
import urllib
import sys

def update_single_submission_status(status, add_annotations, to_public=False, force_change_annotation_acl=False):
	"""
	This will update a single submission's status
	
	param:
		status: syn.getSubmissionStatus()
		add_annotations: Annotations that you want to add in dict or submission status annotations format.
			  			 If dict, all submissions will be added as private submissions
		to_public: change these annotations from private to public (default is False)
		force_change_annotation_acl: Force change the annotation from private to public and vice versa
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

def get_challengeid(syn, entity):
	"""
	Function that gets the challenge id for a project

	params:
		entity: An Entity or Synapse ID to lookup
	"""
	synid = synapseclient.utils.id_of(entity)
	challenge_obj = syn.restGET("/entity/%s/challenge" % synid)
	return(challenge_obj)

def _change_annotation_acl(annotations, key, annotation_type, is_private=True):
	'''
	Helper function to locate the existing annotation

	params:
		annotations: submission status annotations
		key: key of the annotation
		annotation_type: stringAnnos, doubleAnnos or longAnnos
		is_private: whether the annotation is private or not, default to True

	'''
	if annotations.get(annotation_type) is not None:
		check = list(filter(lambda x: x.get('key') == key, annotations[annotation_type]))
		if len(check) > 0:
			check[0]['isPrivate'] = is_private
	return(annotations)


def change_submission_annotation_acl(status, annotations, is_private=False):
	"""
	Function to change the acl of a list of known annotation keys on one submission
	
	param:
		status: syn.getSubmissionStatus()
		annotations: list of annotation keys to make public
		is_private: whether the annotation is private or not, default to True
	"""
	submission_annotations = status.annotations
	for key in annotations:
		submission_annotations = _change_annotation_acl(submission_annotations, key, "stringAnnos",is_private)
		submission_annotations = _change_annotation_acl(submission_annotations, key, "doubleAnnos",is_private)
		submission_annotations = _change_annotation_acl(submission_annotations, key, "longAnnos",is_private)
	status.annotations = submission_annotations
	syn.store(status)


def change_all_submissions_annotation_acl(syn, evaluationid, annotations, status='SCORED', is_private=False):
	"""
	Function to change the acl of a list of known annotation keys on all submissions of a evaluation
	
	params:
		syn: synapse object
		evaluationid: evaluation id
		annotations: list of annotation keys to make public
		status: ALL, VALIDATED, INVALID
		is_private: whether the annotation is private or not, default to True
	"""
	status = None if status == 'ALL' else status
	bundle = syn.getSubmissionBundles(evaluationid,status=status)
	for sub, status in bundle:
		change_submission_annotation_acl(status, annotations, is_private=is_private)
