"""Base synapse service - modelled from swagger-codegen"""
import datetime
import pprint
import typing
from typing import Generic, Union

import six

T = typing.TypeVar('T')


def _deserialize(data: Union[dict, list, str], klass):
    """Deserializes dict, list, str into an object.

    Args:
        data: dict, list or str.
        klass: class literal, or string of class name.

    Returns:
        object

    """
    if data is None:
        return None

    if klass in six.integer_types or klass in (float, str, bool):
        return _deserialize_primitive(data, klass)
    if klass == object:
        return _deserialize_object(data)
    if klass == datetime.date:
        return deserialize_date(data)
    if klass == datetime.datetime:
        return deserialize_datetime(data)
    if isinstance(klass, Generic):
        if klass.__extra__ == list:
            return _deserialize_list(data, klass.__args__[0])
        if klass.__extra__ == dict:
            return _deserialize_dict(data, klass.__args__[1])
    return deserialize_model(data, klass)


def _deserialize_primitive(data, klass) -> Union[int, float, str, bool]:
    """Deserializes to primitive type.

    Args:
        data: data to deserialize.
        klass: class literal.

    Returns:
        int, long, float, str, bool.

    """
    try:
        value = klass(data)
    except UnicodeEncodeError:
        value = six.u(data)
    except TypeError:
        value = data
    return value


def _deserialize_object(value):
    """Return an original value.

    Returns:
        object

    """
    return value


def deserialize_date(string: str) -> datetime.date:
    """Deserializes string to date.

    Args:
        string: str.

    Returns:
        date

    """
    try:
        from dateutil.parser import parse
        return parse(string).date()
    except ImportError:
        return string


def deserialize_datetime(string: str) -> datetime.datetime:
    """Deserializes string to datetime.
    The string should be in iso8601 datetime format.

    Args:
        string: str.

    Returns:
        datetime
    """
    try:
        from dateutil.parser import parse
        return parse(string)
    except ImportError:
        return string


def deserialize_model(data: Union[dict, list], klass):
    """Deserializes list or dict to model.

    Args:
        data: dict, list.
        klass: class literal.

    Returns:
        model object.

    """
    instance = klass()

    if not instance.openapi_types:
        return data

    for attr, attr_type in six.iteritems(instance.openapi_types):
        if data is not None \
                and instance.attribute_map[attr] in data \
                and isinstance(data, (list, dict)):
            value = data[instance.attribute_map[attr]]
            setattr(instance, attr, _deserialize(value, attr_type))

    return instance


def _deserialize_list(data: list, boxed_type) -> list:
    """Deserializes a list and its elements.

    Args:
        data: list to deserialize.
        boxed_type: class literal

    Returns:
        deserialized list

    """
    return [_deserialize(sub_data, boxed_type)
            for sub_data in data]


def _deserialize_dict(data: dict, boxed_type) -> dict:
    """Deserializes a dict and its elements.

    Args:
        data: dict to deserialize.
        boxed_type: class literal.

    Returns:
        deserialized dict

    """
    return {k: _deserialize(v, boxed_type)
            for k, v in six.iteritems(data)}


class Service:
    """Base service

    Attributes:
        openapi_types: The key is attribute name and the
                       value is attribute type.
        attribute_map: The key is attribute name and the
                       value is json key in definition.

    """

    openapi_types = {}

    attribute_map = {}

    @classmethod
    def from_dict(cls: typing.Type[T], dikt) -> T:
        """Returns the dict as a model"""
        return deserialize_model(dikt, cls)

    def to_dict(self) -> dict:
        """Returns the model properties as a dict

        Returns:
            dict

        """
        result = {}

        for attr, _ in six.iteritems(self.openapi_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value

        return result

    def to_str(self) -> str:
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self) -> str:
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other) -> bool:
        """Returns true if both objects are equal"""
        return self.__dict__ == other.__dict__
