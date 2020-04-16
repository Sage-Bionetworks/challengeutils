"""Challenge Services"""
import synapseclient
from synapseclient import Synapse

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


class ChallengeApi:
    """Challenge services
    https://docs.synapse.org/rest/index.html#org.sagebionetworks.repo.web.controller.ChallengeController
    Args:
        id: The ID of this Challenge object
        etag: Synapse employs an Optimistic Concurrency Control (OCC)
              scheme to handle concurrent updates.
        projectId: The ID of the Project the challenge is used with.
        participantTeamId: The ID of the Team which users join to participate
                           in the Challenge
    """
    def __init__(self, syn: Synapse = None, id: str = None,
                 projectId: str = None, participantTeamId: str = None):
        """

        """
        if syn is None:
            raise ValueError("Must pass in Synapse connection")
        self.syn = syn
        self._challenge = Challenge(id=id,
                                    projectId=projectId,
                                    participantTeamId=participantTeamId)

    def create_challenge(self):
        """Creates a challenge"""
        challenge = self.syn.restPOST('/challenge',
                                      str(self._challenge))
        return Challenge(**challenge)

    def get_challenge(self):
        """Gets a challenge"""
        if self._challenge.id is not None:
            url = f"/challenge/{self._challenge.id}"
        elif self._challenge.projectId is not None:
            url = f"/entity/{self._challenge.projectId}/challenge"
        else:
            raise ValueError("Must pass in `id` or `projectId`")

        return Challenge(**self.syn.restGET(url))

    def update_challenge(self):
        """Updates a challenge"""
        if self._challenge.id is None:
            raise ValueError("Must pass in `id`")
        challenge = self.syn.restPUT(f'/challenge/{self._challenge.id}',
                                     str(self._challenge))
        return Challenge(**challenge)

    def delete_challenge(self):
        """Deletes a challenge"""
        if self._challenge.id is None:
            raise ValueError("Must pass in `id`")
        return self.syn.restDELETE(f'/challenge/{self._challenge.id}')

    def get_registered_participants(self):
        """Lists participants registered for a challenge"""
        if self._challenge.id is None:
            raise ValueError("Must pass in `id`")
        return self.syn.restGET(f'/challenge/{self._challenge.id}/participant')

    def get_registered_teams(self):
        """Lists teams registered for a challenge"""
        if self._challenge.id is None:
            raise ValueError("Must pass in `id`")
        url = f'/challenge/{self._challenge.id}/challengeTeam'
        return self.syn.restGET(url)
