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


def annotate_submission_with_json(syn, submissionid, annotation_values,
                                  **kwargs):
    """
    ChallengeWorkflowTemplate tool: Annotates submission with annotation
    values from a json file and uses exponential backoff to retry when
    there are concurrent update issues (HTTP 412).

    Args:
        syn: Synapse object
        submissionid: Submission id
        annotation_values: Annotation json file
        **kwargs: is_private: Set annotations acl to private (default is True)
                  force: Force change the annotation from
                         private to public and vice versa.
                  status: A submission status (e.g. RECEIVED, SCORED...)

    Returns:
        synapseclient.SubmissionStatus

    """
    with open(annotation_values) as json_data:
        annotation_json = json.load(json_data)
    sub_status = annotate_submission(syn, submissionid, annotation_json,
                                     **kwargs)
    return sub_status


def annotate_submission(syn, submissionid, annotation_dict,
                        status=None, is_private=True, force=False):
    """Annotate submission with annotation values from a dict

    Args:
        syn: Synapse object
        submissionid: Submission id
        annotation_dict: Annotation dict
        is_private: Set annotations acl to private (default is True)
        force: Force change the annotation from
               private to public and vice versa.
    """
    sub_status = syn.getSubmissionStatus(submissionid)
    # Don't add any annotations that are None or []
    not_add = [None, []]
    annotation_dict = {key: annotation_dict[key] for key in annotation_dict
                       if annotation_dict[key] not in not_add}
    # TODO: Remove once submissionview is fully supported
    sub_status = update_single_submission_status(sub_status, annotation_dict,
                                                 is_private=is_private,
                                                 force=force)
    sub_status = update_submission_status(sub_status, annotation_dict,
                                          status=status)
    return syn.store(sub_status)
