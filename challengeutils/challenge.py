"""Synapse Challenge Services"""
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
    def __init__(self, syn: Synapse):
        self.syn = syn

    def create_challenge(self, teamid: str, projectid: str) -> Challenge:
        """Creates a challenge

        Args:
            teamid: A Synapse Team id
            projectid: A Synapse Project id

        Returns:
            A synapseservices.Challenge

        """
        new_challenge = Challenge(participantTeamId=teamid,
                                  projectId=projectid)
        challenge = self.syn.restPOST('/challenge',
                                      str(new_challenge))
        return Challenge(**challenge)

    def get_challenge(self, challengeid: str = None,
                      projectid: str = None) -> Challenge:
        """Gets a challenge

        Args:
            challengeid: A Synapse Challenge id
            projectId: A Synapse Project id

        Returns:
            A synapseservices.Challenge

        """
        if challengeid is not None:
            url = f"/challenge/{challengeid}"
        elif projectid is not None:
            url = f"/entity/{projectid}/challenge"
        else:
            raise ValueError("Must pass in `challengeid` or `projectid`")

        return Challenge(**self.syn.restGET(url))

    def update_challenge(self, challengeid: str, teamid: str = None,
                         projectid: str = None) -> Challenge:
        """Updates a Synapse Challenge

        Args:
            challengeid: A Synapse Challenge id
            teamid: A Synapse Team id
            projectid: A Synapse Project id

        Returns:
            A synapseservices.Challenge

        """
        new_challenge = Challenge(id=challengeid,
                                  participantTeamId=teamid,
                                  projectId=projectid)
        challenge = self.syn.restPUT(f'/challenge/{challengeid}',
                                     str(new_challenge))
        return Challenge(**challenge)

    def delete_challenge(self, challengeid: str):
        """Deletes a Synapse Challenge

        Args:
            challengeid: A Synapse Challenge id
        """
        return self.syn.restDELETE(f'/challenge/{challengeid}')

    def get_registered_participants(self, challengeid: str) -> list:
        """Get participants registered for a challenge

        Args:
            challengeid: A Synapse Challenge id

        Returns:
            Registered participants

        """
        url = f'/challenge/{challengeid}/participant'
        return self.syn._GET_paginated(url)

    def get_registered_teams(self, challengeid: str):
        """Get teams registered for a challenge

        Args:
            challengeid: A Synapse Challenge id

        Returns:
            Registered teams

        """
        url = f'/challenge/{challengeid}/challengeTeam'
        return self.syn._GET_paginated(url)
