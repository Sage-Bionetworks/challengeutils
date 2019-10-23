from .base_service import Service, deserialize_model


class Challenge(Service):
    """Challenge - Settings for a Challenge Project
    
    Args:
        id: The ID of this Challenge object
        etag: Synapse employs an Optimistic Concurrency Control (OCC) scheme to handle concurrent updates.
        projectId: The ID of the Project the challenge is used with.
        participantTeamId: The ID of the Team which users join to participate in the Challenge
    """
    def __init__(self, id=None, projectId=None, etag=None,
                 participantTeamId=None):

        self.openapi_types = {
            'id': str,
            'projectid': str,
            'etag': str,
            'participant_teamid': str
        }

        self.attribute_map = {
            'id': 'id',
            'projectid': 'projectId',
            'etag': 'etag',
            'participant_teamid': 'participantTeamId'
        }

        self._id = id
        self._projectid = projectId
        self._etag = etag
        self._participant_teamid = participantTeamId


    @classmethod
    def from_dict(cls, dikt) -> 'Challenge':
        """Returns the dict as a model
        Args:
            dikt: A dict.

        Returns:
            The Challenge settings
        """
        return deserialize_model(dikt, cls)

    @property
    def id(self):
        """Gets the id of this Challenge.

        Returns:
            The id of this Challenge
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this Challenge.

        Args:
            id: The ID of this Challenge
        """

        self._id = id

    @property
    def projectid(self):
        """Gets the projectid of this Challenge.

        Returns:
            The projectid of this Challenge
        """
        return self._projectid

    @projectid.setter
    def projectid(self, projectid):
        """Sets the projectid of this Challenge.

        Args:
            projectid: The projectid of this Challenge
        """
        if projectid is None:
            raise ValueError("Invalid value for `projectid`, must not be `None`")  # noqa: E501

        self._projectid = projectid

    @property
    def etag(self):
        """Gets the etag of this Challenge.

        Returns:
            The etag of this Challenge
        """
        return self._etag

    @etag.setter
    def etag(self, etag):
        """Sets the etag of this Challenge.

        Args:
            etag: The etag of this Challenge
        """
        self._etag = etag

    @property
    def participant_teamid(self):
        """Gets the etag of this Challenge.

        Returns:
            The etag of this Challenge
        """
        return self._etag

    @participant_teamid.setter
    def participant_teamid(self, participant_teamid):
        """Sets the participant_teamid of this Challenge.

        Args:
            etag: The participant_teamid of this Challenge
        """
        self._participant_teamid = participant_teamid
