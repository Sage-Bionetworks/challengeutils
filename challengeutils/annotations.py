"""
Updating submission annotations
Deprecate many of these functions once synapseclient==2.1.0
"""
import collections
import datetime
import json
import typing

from synapseclient import Entity, SubmissionStatus
from synapseclient.core.utils import (to_unix_epoch_time,
                                      from_unix_epoch_time,
                                      to_list, id_of)

from .utils import update_single_submission_status


# TODO: Remove once synapseclient==2.1.0
def _identity(x):
    return x


# TODO: Remove once synapseclient==2.1.0
def raise_anno_type_error(anno_type: str):
    raise ValueError(f"Unknown type in annotations response: {anno_type}")


# TODO: Remove once synapseclient==2.1.0
ANNO_TYPE_TO_FUNC: typing.Dict[
    str, typing.Callable[
        [str],
        typing.Union[str, int, float, datetime.datetime]
    ]] = \
    collections.defaultdict(
        raise_anno_type_error,
        {
            'STRING': _identity,
            'LONG': int,
            'DOUBLE': float,
            'TIMESTAMP_MS': lambda timestr: from_unix_epoch_time(int(timestr))
        }
    )


# TODO: Remove once synapseclient==2.1.0
def is_synapse_annotations(annotations: typing.Mapping):
    """Tests if the given object is a Synapse-style Annotations object."""
    if not isinstance(annotations, collections.abc.Mapping):
        return False
    return annotations.keys() >= {'id', 'etag', 'annotations'}


# TODO: Remove once synapseclient==2.1.0
def _annotation_value_list_element_type(annotation_values: typing.List):
    if not annotation_values:
        raise ValueError("annotations value list can not be empty")

    first_element_type = type(annotation_values[0])

    if all(isinstance(x, first_element_type) for x in annotation_values):
        return first_element_type

    return object


# TODO: Remove once synapseclient==2.1.0
class Annotations(dict):
    """
    Represent Synapse Entity annotations as a flat dictionary with
    the system assigned properties id, etag as object attributes.
    """
    id: str
    etag: str

    def __init__(self, id: typing.Union[str, int, Entity],
                 etag: str, values: typing.Dict = None, **kwargs):
        """
        Create an Annotations object taking key value pairs from a dictionary
        or from keyword arguments.
        System properties id, etag, creationDate and uri become attributes of
        the object.

        :param id:  A Synapse ID, a Synapse Entity object, a plain dictionary
                    in which 'id' maps to a Synapse ID
        :param etag: etag of the Synapse Entity
        :param values:  (Optional) dictionary of values to be copied into
                        annotations

        :param **kwargs: additional key-value pairs to be added as
                          annotations
        """
        super().__init__()

        self.id = id
        self.etag = etag

        if values:
            self.update(values)
        if kwargs:
            self.update(kwargs)

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        if value is None:
            raise ValueError("id must not be None")
        self._id = id_of(value)

    @property
    def etag(self):
        return self._etag

    @etag.setter
    def etag(self, value):
        if value is None:
            raise ValueError("etag must not be None")
        self._etag = str(value)


# TODO: Remove once synapseclient==2.1.0
def to_synapse_annotations(
        annotations: Annotations) -> typing.Dict[str, typing.Any]:
    """Transforms a simple flat dictionary to a Synapse-style Annotation
    object.
    https://rest-docs.synapse.org/rest/org/sagebionetworks/repo/model/annotation/v2/Annotations.html
    """

    if is_synapse_annotations(annotations):
        return annotations
    synapse_annos = {}

    if not isinstance(annotations, Annotations):
        raise TypeError("annotations must be a synapseclient.Annotations "
                        "object with 'id' and 'etag' attributes")

    synapse_annos['id'] = annotations.id
    synapse_annos['etag'] = annotations.etag

    nested_annos = synapse_annos.setdefault('annotations', {})
    for key, value in annotations.items():
        elements = to_list(value)
        element_cls = _annotation_value_list_element_type(elements)
        if issubclass(element_cls, str):
            nested_annos[key] = {'type': 'STRING',
                                 'value': elements}
        elif issubclass(element_cls, bool):
            nested_annos[key] = {'type': 'STRING',
                                 'value': [str(e).lower() for e in elements]}
        elif issubclass(element_cls, int):
            nested_annos[key] = {'type': 'LONG',
                                 'value': [str(e) for e in elements]}
        elif issubclass(element_cls, float):
            nested_annos[key] = {'type': 'DOUBLE',
                                 'value': [str(e) for e in elements]}
        elif issubclass(element_cls, (datetime.date, datetime.datetime)):
            nested_annos[key] = {'type': 'TIMESTAMP_MS',
                                 'value': [str(to_unix_epoch_time(e))
                                           for e in elements]}
        else:
            nested_annos[key] = {'type': 'STRING',
                                 'value': [str(e) for e in elements]}
    return synapse_annos


# TODO: Remove once synapseclient==2.1.0
def from_synapse_annotations(
        raw_annotations: typing.Dict[str, typing.Any]) -> Annotations:
    """Transforms a Synapse-style Annotation object to a simple flat
    dictionary."""
    if not is_synapse_annotations(raw_annotations):
        raise ValueError('Unexpected format of annotations from Synapse. '
                         'Must include keys: "id", "etag", and "annotations"')

    annos = Annotations(raw_annotations['id'], raw_annotations['etag'])
    for key, value_and_type in raw_annotations['annotations'].items():
        key: str
        conversion_func = ANNO_TYPE_TO_FUNC[value_and_type['type']]
        annos[key] = [conversion_func(v) for v in value_and_type['value']]

    return annos


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
