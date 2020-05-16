"""Synapse Challenge Services"""
import json
from typing import Union, Iterator

from synapseclient import Project, Synapse, Team
from synapseclient.core.utils import id_of

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
        challenge_object = {'participantTeamId': teamid,
                            'projectId': projectid}
        challenge = self.syn.restPOST('/challenge',
                                      json.dumps(challenge_object))
        return Challenge(**challenge)

    def get_registered_challenges(self,
                                  participantId: str) -> Iterator[Challenge]:
        """Gets a list of challenges a participant is registered to

        Args:
            participantId: A Synapse User Id

        Yields:
            A synapseservices.Challenge

        """
        challenges = self.syn._GET_paginated(
            f'/challenge?participantId={participantId}'
        )
        for challenge in challenges:
            yield Challenge(**challenge)

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
        challenge_object = {'id': challengeid,
                            'participantTeamId': teamid,
                            'projectId': projectid}
        challenge = self.syn.restPUT(f'/challenge/{challengeid}',
                                     json.dumps(challenge_object))
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

    def register_team(self, challengeid: str, teamid: str):
        """Register team

        Args:
            challengeid: A Synapse challenge id
            teamid: A Synapse Team id

        Returns:
            A Synapse team

        """
        team_dict = {'challengeId': challengeid, 'teamId': teamid}
        return self.syn.restPOST(f'/challenge/{challengeid}/challengeTeam',
                                 json.dumps(team_dict))


def get_registered_challenges(syn: Synapse,
                              userid: str = None) -> Iterator[Project]:
    """Get the Synapse Challenge Projects a user is registered to.
    Defaults to the logged in synapse user.

    Args:
        syn: Synapse connection
        userid: Specify userid if you want to know the challenges
                another Synapse user is registered to.

    Yields:
        A synapseclient.Project

    """
    challenge_api = ChallengeApi(syn=syn)
    # This will return the logged in user profile if None is passed in
    profile = syn.getUserProfile(userid)
    userid = profile.ownerId
    registered = challenge_api.get_registered_challenges(participantId=userid)
    for challenge in registered:
        challenge_ent = syn.get(challenge.projectId)
        print(challenge_ent.name)
        yield challenge_ent


def get_challenge(syn: Synapse, project: Union[Project, str]) -> Challenge:
    """Get the Challenge associated with a Project.

    See the definition of a Challenge object here:
    https://docs.synapse.org/rest/org/sagebionetworks/repo/model/Challenge.html

    Args:
        syn: Synapse connection
        project: A synapseclient.Project or its id

    Returns:
        Challenge object

    """
    synid = id_of(project)
    challenge_api = ChallengeApi(syn=syn)
    challenge_obj = challenge_api.get_challenge(projectid=synid)
    return challenge_obj


def create_challenge(syn: Synapse, project: Union[Project, str],
                     team: Union[Team, str]) -> Challenge:
    """Creates Challenge associated with a Project

    Args:
        syn: Synapse connection
        project: A synapseclient.Project or its id
        team: A synapseclient.Team or its id

    Returns:
        Challenge object

    """
    synid = id_of(project)
    teamid = id_of(team)

    challenge_api = ChallengeApi(syn=syn)
    challenge_obj = challenge_api.create_challenge(projectid=synid,
                                                   teamid=teamid)
    return challenge_obj
