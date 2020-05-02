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
        """The `id` property of this Challenge."""
        return self._id

    @id.setter
    def id(self, value: str):
        self._id = value

    @property
    def projectId(self) -> str:
        """The `projectId` property of this Challenge."""
        return self._projectId

    @projectId.setter
    def projectId(self, value: str):
        self._projectId = value

    @property
    def etag(self) -> str:
        """The `etag` property of this Challenge."""
        return self._etag

    @etag.setter
    def etag(self, value: str):
        self._etag = value

    @property
    def participantTeamId(self) -> str:
        """The `participantTeamId` property of this Challenge."""
        return self._participantTeamId

    @participantTeamId.setter
    def participantTeamId(self, value: str):
        self._participantTeamId = value
