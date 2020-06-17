"""
Updating submission annotations
Deprecate many of these functions once synapseclient==2.1.0
"""
import json
import typing

from synapseclient import SubmissionStatus, Annotations
from synapseclient.annotations import (is_synapse_annotations,
                                       to_synapse_annotations,
                                       from_synapse_annotations)

from .utils import update_single_submission_status


def _convert_to_annotation_cls(
        sub_status: SubmissionStatus,
        values: typing.Union[Annotations, dict]) -> Annotations:
    """Convert synapse style annotation or dict to synapseclient.Annotation

    Args:
        sub_status:  A synapseclient.SubmissionStatus
        values:  A synapseclient.Annotations or dict

    Returns:
        A synapseclient.Annotations

    """
    if isinstance(values, Annotations):
        return values
    if is_synapse_annotations(values):
        values = from_synapse_annotations(values)
    else:
        values = Annotations(id=sub_status.id,
                             etag=sub_status.etag,
                             values=values)
    return values


def update_submission_status(sub_status: SubmissionStatus,
                             values: typing.Union[Annotations, dict],
                             status: str = None) -> SubmissionStatus:
    """Updates submission status and annotations

    Args:
        sub_status:  A synapseclient.SubmissionStatus
        values:  A synapseclient.Annotations or dict
        status: A submission status (e.g. RECEIVED, SCORED...)

    Returns:
        A updated synapseclient.SubmissionStatus

    """
    if status is not None:
        sub_status.status = status
    existing = sub_status.get("submissionAnnotations", {})
    # Convert to synapseclient.Annotation class
    existing_annotations = _convert_to_annotation_cls(sub_status, existing)
    new_annotations = _convert_to_annotation_cls(sub_status, values)
    # Can use dict.update to update annotations
    existing_annotations.update(new_annotations)
    # Must turn synapseclient.Annotation into a synapse style annotations
    syn_annotations = to_synapse_annotations(existing_annotations)
    sub_status.submissionAnnotations = syn_annotations
    return sub_status


class mock_response:
    """Mocked status code to return"""
    status_code = 200


def annotate_submission_with_json(syn, submissionid, annotation_values,
                                  status=None, is_private=True,
                                  force=False):
    '''
    ChallengeWorkflowTemplate tool: Annotates submission with annotation
    values from a json file and uses exponential backoff to retry when
    there are concurrent update issues (HTTP 412).  Must return a object
    with status_code that has a range between 200-209

    Args:
        syn: Synapse object
        submissionid: Submission id
        annotation_values: Annotation json file
        status: A submission status (e.g. RECEIVED, SCORED...)
        is_private: Set annotations acl to private (default is True)
        force: Force change the annotation from
               private to public and vice versa.

    Returns:
        mocked response object (200)
    '''
    sub_status = syn.getSubmissionStatus(submissionid)
    with open(annotation_values) as json_data:
        annotation_json = json.load(json_data)
    # TODO: Remove once submissionview is fully supported
    sub_status = update_single_submission_status(sub_status, annotation_json,
                                                 is_private=is_private,
                                                 force=force)
    sub_status = update_submission_status(sub_status, annotation_json,
                                          status=status)
    sub_status = syn.store(sub_status)
    # TODO: no need to return this (with_retry works without code
    # in synapseclient==2.1.0)
    return mock_response
