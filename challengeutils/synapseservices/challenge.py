"""Challenge Services"""
from .base_service import Service


class Challenge(Service):
    """Synapse Challenge object
    https://docs.synapse.org/rest/org/sagebionetworks/repo/model/Challenge.html

    Args:
        id: The ID of this Challenge object
        etag: Synapse employs an Optimistic Concurrency Control (OCC)
              scheme to handle concurrent updates.
        projectId: The ID of the Project the challenge is used with.
        participantTeamId: The ID of the Team which users join to participate
                           in the Challenge
    """
    def __init__(self, id: str = None, projectId: str = None, etag:
                 str = None, participantTeamId: str = None):

        self.openapi_types = {
            'id': str,
            'projectId': str,
            'etag': str,
            'participantTeamId': str
        }

        self.attribute_map = {
            'id': 'id',
            'projectId': 'projectId',
            'etag': 'etag',
            'participantTeamId': 'participantTeamId'
        }

        self._id = id
        self._projectId = projectId
        self._etag = etag
        self._participantTeamId = participantTeamId

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
    def projectId(self):
        """Gets the id of this Activity.
        :return: The id of this Activity.
        :rtype: str
        """
        return self._projectId

    @projectId.setter
    def projectId(self, projectId):
        """Sets the id of this Activity.
        :param id: The id of this Activity.
        :type id: str
        """
        self._projectId = projectId

    @property
    def etag(self):
        """Gets the id of this Activity.
        :return: The id of this Activity.
        :rtype: str
        """
        return self._etag

    @etag.setter
    def etag(self, etag):
        """Sets the id of this Activity.
        :param id: The id of this Activity.
        :type id: str
        """
        self._id = etag


    @property
    def participantTeamId(self):
        """Gets the id of this Activity.
        :return: The id of this Activity.
        :rtype: str
        """
        return self._participantTeamId

    @participantTeamId.setter
    def participantTeamId(self, participantTeamId):
        """Sets the id of this Activity.
        :param id: The id of this Activity.
        :type id: str
        """
        self._participantTeamId = participantTeamId
