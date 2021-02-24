"""
Challenge utility functions
"""
import datetime
import json
import logging
import sys
import urllib

import synapseclient
from synapseclient.annotations import (is_submission_status_annotations,
                                       to_submission_status_annotations)
from synapseclient.core.exceptions import SynapseHTTPError
from synapseclient.core.utils import id_of

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO: Deprecate once fully using submissionviews
def _switch_annotation_permission(add_annotations,
                                  existing_annotations,
                                  force=False):
    '''
    Switch annotation permissions
    If you add a private annotation that appears in the public annotation,
    it should throw an error, or switch permissions

    Args:
        add_annotations: Annotations to add
        existing_annotations: Existing annotations (of the opposite annotation
                              permissions)
        force: Force the annotation permission to change. Default is False.

    Returns:
        Existing annotations
    '''
    check_key = [key in add_annotations for key in existing_annotations]
    if sum(check_key) == 0:
        pass
    elif sum(check_key) > 0 and force:
        # Filter out the annotations that have changed ACL
        existing_annotations = {key: existing_annotations[key]
                                for key in existing_annotations
                                if key not in add_annotations}
    else:
        change_keys = [key for key in existing_annotations
                       if key in add_annotations]
        raise ValueError(
            "You are trying to change the ACL of these annotation key(s): {}."
            " Either change the annotation key or specify "
            "force=True".format(", ".join(change_keys)))
    return existing_annotations

# TODO: Deprecate once fully using submissionviews
def _submission_annotations_to_dict(annotations, is_private=True):
    '''
    Convert private / public submission status objects to dictionary

    Args:
        annotations: Synapse submission status object
        is_private: Private or public annotations

    Returns:
        dictionary with annotation key value pairs
    '''
    annotation_dict = {annotation['key']: annotation['value']
                       for annotation_type in annotations
                       for annotation in annotations[annotation_type]
                       if annotation_type not in ['scopeId', 'objectId'] and
                       annotation['isPrivate'] == is_private}
    return annotation_dict

# TODO: Deprecate once fully using submissionviews
def update_single_submission_status(status, add_annotations, is_private=True,
                                    force=False):
    """
    This will update a single submission's status

    Args:
        status: syn.getSubmissionStatus()
        add_annotations: Annotations that you want to add in dict or
                         submission status annotations format.
                         If dict, all submissions will be added as
                         private submissions
        is_private: Annotations are set to private (default is True)
        force: Force update the annotation from
               private to public and vice versa.
    Returns:
        Updated submission status
    """
    existing_annots = status.get("annotations", dict())
    private_annotations = _submission_annotations_to_dict(existing_annots,
                                                          is_private=True)

    public_annotations = _submission_annotations_to_dict(existing_annots,
                                                         is_private=False)

    if not is_submission_status_annotations(add_annotations):
        private_added_annotations = add_annotations if is_private else dict()
        public_added_annotations = dict() if is_private else add_annotations
    else:
        private_added_annotations = _submission_annotations_to_dict(
            add_annotations, is_private=True)

        public_added_annotations = _submission_annotations_to_dict(
            add_annotations, is_private=False)

    # If you add a private annotation that appears in the public annotation,
    # it switches
    private_annotations = _switch_annotation_permission(public_added_annotations,
                                                        private_annotations,
                                                        force)

    public_annotations = _switch_annotation_permission(private_added_annotations,
                                                       public_annotations,
                                                       force)

    private_annotations.update(private_added_annotations)
    public_annotations.update(public_added_annotations)

    priv = to_submission_status_annotations(private_annotations,
                                            is_private=True)
    pub = to_submission_status_annotations(public_annotations,
                                           is_private=False)
    # Combined private and public annotations into
    # one Submission.Status.annotation
    combined_annotations = {'stringAnnos': [],
                            'longAnnos': [],
                            'doubleAnnos': []}
    for annotation_type in ['stringAnnos', 'longAnnos', 'doubleAnnos']:
        private_annotation = priv.get(annotation_type)
        public_annotation = pub.get(annotation_type)
        private_annotation_exists = private_annotation is not None
        public_annotation_exists = public_annotation is not None
        if private_annotation_exists:
            combined_annotations[annotation_type].extend(private_annotation)
        if public_annotation_exists:
            combined_annotations[annotation_type].extend(public_annotation)
        # Remove annotation key if doesn't exist
        if not private_annotation_exists and not public_annotation_exists:
            combined_annotations.pop(annotation_type)
    status['annotations'] = combined_annotations
    return status


# TODO: Deprecate once fully using submissionviews
def evaluation_queue_query(syn, uri, limit=20, offset=0):
    """
    This is to query the evaluation queue service.
    The limit parameter is set at 20 by default.
    Using a larger limit results in fewer calls
    to the service, but if responses are large enough to be a
    burden on the service they may be truncated.

    Args:
        syn:     A Synapse object
        uri:     A URI for evaluation queues (select * from evaluation_12345)
        limit:   How many records should be returned per request
        offset:  At what record offset from the first should iteration start

    Yields:
        dict: A generator over some paginated results
    """

    prev_num_results = sys.maxsize
    while prev_num_results > 0:
        rest_uri = "/evaluation/submission/query?query=" + \
            urllib.parse.quote_plus("{} limit {} offset {}".format(
                uri, limit, offset))
        page = syn.restGET(rest_uri)
        # results = page['results'] if 'results' in page else page['children']
        results = [{page['headers'][index]:value
                    for index, value in enumerate(row['values'])}
                   for row in page['rows']]
        prev_num_results = len(results)
        for result in results:
            offset += 1
            yield result


def _change_annotation_acl(annotations, key, annotation_type, is_private=True):
    '''
    Helper function to locate the existing annotation

    Args:
        annotations: submission status annotations
        key: key of the annotation
        annotation_type: stringAnnos, doubleAnnos or longAnnos
        is_private: whether the annotation is private or not, default to True

    Returns:
        Updated annotation key ACL

    '''
    if annotations.get(annotation_type) is not None:
        check = list(filter(lambda x: x.get('key') == key,
                            annotations[annotation_type]))
        if check:
            check[0]['isPrivate'] = is_private
    return annotations

# TODO: Deprecate once fully using submissionviews
def change_submission_annotation_acl(status, annotations, is_private=False):
    """
    Function to change the acl of a list of known annotation keys
    on one submission

    Args:
        status: syn.getSubmissionStatus()
        annotations: list of annotation keys to make public
        is_private: whether the annotation is private or not, default to True

    Returns:
        Submission status with new submission annotation ACLs
    """
    submission_annotations = status.annotations
    for key in annotations:
        submission_annotations = _change_annotation_acl(
            submission_annotations, key, "stringAnnos", is_private)
        submission_annotations = _change_annotation_acl(
            submission_annotations, key, "doubleAnnos", is_private)
        submission_annotations = _change_annotation_acl(
            submission_annotations, key, "longAnnos", is_private)
    status.annotations = submission_annotations
    return status

# TODO: Deprecate once fully using submissionviews
def update_all_submissions_annotation_acl(syn, evaluationid, annotations,
                                          status='SCORED', is_private=False):
    """
    Function to change the acl of a list of known annotation keys on
    all submissions of a evaluation

    Args:
        syn: synapse object
        evaluationid: evaluation id
        annotations: list of annotation keys to make public
        status: ALL, VALIDATED, INVALID
        is_private: whether the annotation is private or not, default to True
    """
    status = None if status == 'ALL' else status
    bundle = syn.getSubmissionBundles(evaluationid, status=status)
    for _, status in bundle:
        new_status = change_submission_annotation_acl(status, annotations,
                                                      is_private=is_private)
        syn.store(new_status)


def change_submission_status(syn, submissionid, status='RECEIVED'):
    '''
    Function to change a submission status

    Args:
        syn: Synapse object
        submissionid: Id of a submission
        status: Submission status to change a submission to

    Returns:
        Updated submission status
    '''
    sub_status = syn.getSubmissionStatus(submissionid)
    sub_status.status = status
    sub_status = syn.store(sub_status)
    return sub_status

# TODO: Can possibly deprecate once using submissionview
def change_all_submission_status(syn, evaluationid, submission_status='SCORED',
                                 change_to_status='VALIDATED'):
    '''
    Function to change submission status of all submissions in a queue
    The defaults is to change submissions from SCORED -> VALIDATED
    This function can be useful for 'rescoring' submissions

    Args:
        syn: Synapse object
        evaluationid: Id of an Evaluation queue
        submission_status: Submissions with this status that you want to
                           change. Default is SCORED.
        change_to_status: Submission status to change a submission to.
                          Default is VALIDATED.
    '''
    submission_bundle = syn.getSubmissionBundles(evaluationid,
                                                 status=submission_status)
    for _, status in submission_bundle:
        status.status = change_to_status
        syn.store(status)


def _check_date_range(date_str, start_datetime, end_datetime):
    '''
    Helper function to check if the date is within range
    Note: the date and time is in UTC

    Args:
        date_str: date string
        start_datetime: start date time in YYYY-MM-DD H:M format,
                        example: 2019-01-01 1:00
        end_datetime: end date time in YYYY-MM-DD H:M format,
                      example: 2019-01-01 23:59

    Returns:
        boolean
    '''
    result = True
    if start_datetime is not None or end_datetime is not None:
        date_obj = datetime.datetime.strptime(date_str,
                                              '%Y-%m-%dT%H:%M:%S.%fZ')
        if start_datetime is not None:
            start_obj = datetime.datetime.strptime(start_datetime,
                                                   '%Y-%m-%d %H:%M')
            result = date_obj >= start_obj
        if end_datetime is not None:
            end_obj = datetime.datetime.strptime(end_datetime,
                                                 '%Y-%m-%d %H:%M')
            result = date_obj <= end_obj
    return result


def _get_contributors(syn, evaluationid, status,
                      start_datetime, end_datetime):
    '''
    Helper function to get contributors from a given evaluation id.
    Note: the date and time is in UTC

    Args:
        syn: Synapse object
        evaluationid: evaluation id
        submission_status: Submission status
        start_datetime: start date time in YYYY-MM-DD H:M format,
                        example: 2019-01-01 23:00
        end_datetime: end date time in YYYY-MM-DD H:M format,
                      example: 2019-01-01 23:59

    Returns:
        Set of contributors' user ids
    '''
    bundles = syn.getSubmissionBundles(evaluationid, status=status)
    contributors = set()
    for sub, _ in bundles:
        if _check_date_range(sub.createdOn, start_datetime, end_datetime):
            principalids = set(contributor['principalId']
                               for contributor in sub.contributors)
            contributors.update(principalids)
    return contributors


def get_contributors(syn, evaluationids, status='SCORED',
                     start_datetime=None, end_datetime=None):
    '''
    Function to get contributors from a list of evaluation ids
    Note: the date and time is in UTC

    Args:
        syn: Synapse object
        evaluationids: a list of evaluation ids
        status: Submission status. Default = SCORED
        start_datetime: start date time in YYYY-MM-DD H:M format,
                        example: 2019-01-01 1:00
        end_datetime: end date time in YYYY-MM-DD H:M format,
                      example: 2019-01-01 23:59

    Returns:
        Set of contributors' user ids
    '''
    all_contributors = set()
    for evaluationid in evaluationids:
        contributors = _get_contributors(syn, evaluationid, status,
                                         start_datetime, end_datetime)
        all_contributors = all_contributors.union(contributors)
    return all_contributors


def list_evaluations(syn, project):
    '''
    List evaluation queues of a Synapse project

    Args:
        syn: Synapse object
        project: Synapse id/entity of project
    '''
    evaluations = syn.getEvaluationByContentSource(project)
    for evaluation in evaluations:
        logger.info(
            "Evaluation- {name}({evalid})".format(name=evaluation.name,
                                                  evalid=evaluation.id))


def download_submission(syn, submissionid, download_location=None):
    '''
    Download submission and return json

    Args:
        syn: Synapse object
        submissionid: Submission id
        download_location: Location to download submission

    Returns:
        dict: submission json results
    '''
    sub = syn.getSubmission(submissionid, downloadLocation=download_location)
    entity = sub['entity']
    result = {'docker_repository': sub.get("dockerRepositoryName"),
              'docker_digest': sub.get("dockerDigest"),
              'entity_id': entity['id'],
              'entity_version': entity.get('versionNumber'),
              'entity_type': entity.get('concreteType'),
              'evaluation_id': sub['evaluationId'],
              'file_path': sub['filePath']}
    return result


def _get_submitter_name(syn, submitterid):
    """Get the Synapse team name or the username given a submitterid

    Args:
        syn: Synapse object
        submitterid: submitter id

    Returns:
        username or teamname
    """

    try:
        user = syn.getUserProfile(submitterid)
        submitter_name = user['userName']
    except SynapseHTTPError:
        team = syn.getTeam(submitterid)
        submitter_name = team['name']
    return submitter_name


def delete_submission(syn, submissionid):
    """Deletes a submission

    Args:
        syn: Synapse object
        submissionid: Id of a submission

    """
    sub = syn.getSubmission(submissionid, downloadFile=False)
    syn.delete(sub)
