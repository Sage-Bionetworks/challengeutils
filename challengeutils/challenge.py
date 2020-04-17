"""Challenge API"""
from synapseclient import Synapse

from .synapseservices.challenge import Challenge


class ChallengeApi:
    """Challenge services
    https://docs.synapse.org/rest/index.html#org.sagebionetworks.repo.web.controller.ChallengeController

    Args:
        id: The ID of this Challenge object
        project: synapseclient.Project or its id
        team: synapseclient.Team or its id

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
