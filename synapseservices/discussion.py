from .base_service import Service, deserialize_model


class Forum(Service):
    def __init__(self, id=None, projectId=None, etag=None):

        self.openapi_types = {
            'id': str,
            'projectid': str,
            'etag': str
        }

        self.attribute_map = {
            'id': 'id',
            'projectid': 'projectId',
            'etag': 'etag'
        }

        self._id = id
        self._projectid = projectId
        self._etag = etag

    @classmethod
    def from_dict(cls, dikt) -> 'Forum':
        """Returns the dict as a model
        :param dikt: A dict.
        :type: dict
        :return: The Activity of this Activity.  # noqa: E501
        :rtype: Activity
        """
        return deserialize_model(dikt, cls)

    @property
    def id(self):
        """Gets the id of this Activity.
        :return: The id of this Activity.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this Activity.
        :param id: The id of this Activity.
        :type id: str
        """

        self._id = id

    @property
    def projectid(self):
        """Gets the name of this Activity.
        :return: The name of this Activity.
        :rtype: str
        """
        return self._projectid

    @projectid.setter
    def projectid(self, projectid):
        """Sets the name of this Activity.
        :param name: The name of this Activity.
        :type name: str
        """
        if projectid is None:
            raise ValueError("Invalid value for `projectid`, must not be `None`")  # noqa: E501

        self._projectid = projectid

    @property
    def etag(self):
        """Gets the description of this Activity.
        :return: The description of this Activity.
        :rtype: str
        """
        return self._etag

    @etag.setter
    def etag(self, etag):
        """Sets the description of this Activity.
        :param description: The description of this Activity.
        :type description: str
        """

        self._etag = etag
