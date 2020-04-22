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
    def id(self) -> str:
        """Gets the id of this Challenge."""
        return self._id

    @id.setter
    def id(self, id: str) -> str:
        """Sets the id of this Challenge.

        Args:
            The id of this Challenge.

        Returns:
            The id of this Challenge.

        """
        self._id = id

    @property
    def projectId(self) -> str:
        """Gets the id of this Challenge."""
        return self._projectId

    @projectId.setter
    def projectId(self, projectId: str) -> str:
        """Sets the projectId of this Challenge.

        Args:
            The projectId of this Challenge.

        """
        self._projectId = projectId

    @property
    def etag(self) -> str:
        """Gets the etag of this Challenge."""
        return self._etag

    @etag.setter
    def etag(self, etag: str) -> str:
        """Sets the etag of this Challenge.

        Args:
            etag: The etag of this Challenge.

        Returns:
            The etag of this Challenge.

        """
        self._etag = etag

    @property
    def participantTeamId(self) -> str:
        """Gets the participant team id of this Challenge."""
        return self._participantTeamId

    @participantTeamId.setter
    def participantTeamId(self, participantTeamId: str) -> str:
        """Sets the participant team id of this Challenge.

        Args:
            participantTeamId: The participant team id of this Challenge.

        Returns:
            The participant team id of this Challenge.

        """
        self._participantTeamId = participantTeamId
