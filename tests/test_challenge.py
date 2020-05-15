"""Tests challenge services"""
import json
from unittest import mock
from unittest.mock import Mock, patch
import uuid

import synapseclient

from challengeutils import challenge
from challengeutils.synapseservices.challenge import Challenge
from challengeutils.challenge import ChallengeApi


class TestChallengeApi:
    """Tests ChallengeApi class"""
    def setup(self):
        """Setup"""
        self.syn = mock.create_autospec(synapseclient.Synapse)
        self.challengeid = "challenge1"
        self.teamid = "team1"
        self.projectid = "project1"
        self.challenge_dict = {'id': self.challengeid,
                               'participantTeamId': self.teamid,
                               'projectId': self.projectid}
        self.challenge_api = ChallengeApi(self.syn)
        self.input = Challenge(id=self.challengeid,
                               projectId=self.projectid,
                               participantTeamId=self.teamid)

        self.expected = Challenge(**self.challenge_dict)

    def test_get_registered_challenges(self):
        """Tests that a challenge object can be instantiated"""
        challenge_list = [self.challenge_dict]*2
        with patch.object(self.syn, "_GET_paginated",
                          return_value=challenge_list) as patch_restpost:
            challenge_objs = self.challenge_api.get_registered_challenges(
                participantId=2222
            )
            assert list(challenge_objs) == [self.expected]*2
            patch_restpost.assert_called_once_with(
                '/challenge?participantId=2222'
            )

    def test_create_challenge(self):
        """Tests that a challenge object can be instantiated"""
        new_challenge = Challenge(projectId=self.projectid,
                                  participantTeamId=self.teamid)
        challenge_object = {'participantTeamId': self.teamid,
                            'projectId': self.projectid}
        with patch.object(self.syn, "restPOST",
                          return_value=self.challenge_dict) as patch_restpost:
            challenge_obj = self.challenge_api.create_challenge(
                teamid=self.teamid,
                projectid=self.projectid
            )
            assert challenge_obj == self.expected
            patch_restpost.assert_called_once_with(
                '/challenge', json.dumps(challenge_object)
            )

    def test_get_challenge__with_id(self):
        """Tests getting challenge with challenge id"""
        with patch.object(self.syn, "restGET",
                          return_value=self.challenge_dict) as patch_restget:
            challenge_obj = self.challenge_api.get_challenge(
                challengeid=self.challengeid
            )
            assert challenge_obj == self.expected
            patch_restget.assert_called_once_with(
                f"/challenge/{self.challengeid}"
            )

    def test_get_challenge__with_project(self):
        """Tests getting challenge with project id"""
        with patch.object(self.syn, "restGET",
                          return_value=self.challenge_dict) as patch_restget:
            challenge_obj = self.challenge_api.get_challenge(
                projectid=self.projectid
            )
            assert challenge_obj == self.expected
            patch_restget.assert_called_once_with(
                f"/entity/{self.projectid}/challenge"
            )

    def test_update_challenge(self):
        """Tests updating Challenge"""
        challenge_dict = {"id": self.challengeid,
                          "participantTeamId": self.teamid,
                          "projectId": self.projectid}
        with patch.object(self.syn, "restPUT",
                          return_value=self.challenge_dict) as patch_restput:
            challenge_obj = self.challenge_api.update_challenge(
                challengeid=self.challengeid,
                projectid=self.projectid,
                teamid=self.teamid
            )
            assert challenge_obj == self.expected
            patch_restput.assert_called_once_with(
                f'/challenge/{self.challengeid}',
                json.dumps(challenge_dict)
            )

    def test_delete_challenge(self):
        """Tests deleting Challenge"""
        with patch.object(self.syn, "restDELETE") as patch_restdelete:
            self.challenge_api.delete_challenge(challengeid=self.challengeid)
            patch_restdelete.assert_called_once_with(
                f'/challenge/{self.challengeid}'
            )

    def test_get_registered_participants(self):
        """Tests getting registered participants"""
        with patch.object(self.syn, "_GET_paginated") as patch_restget:
            self.challenge_api.get_registered_participants(
                challengeid=self.challengeid
            )
            patch_restget.assert_called_once_with(
                f'/challenge/{self.challengeid}/participant'
            )

    def test_get_registered_teams(self):
        """Tests getting registered teams"""
        with patch.object(self.syn, "_GET_paginated") as patch_restget:
            self.challenge_api.get_registered_teams(
                challengeid=self.challengeid
            )
            patch_restget.assert_called_once_with(
                f'/challenge/{self.challengeid}/challengeTeam'
            )

    def test_register_team(self):
        """Tests registering a team"""
        with patch.object(self.syn, "restPOST") as patch_restpost:
            self.challenge_api.register_team(
                challengeid=self.challengeid,
                teamid=self.teamid
            )
            patch_restpost.assert_called_once_with(
                f'/challenge/{self.challengeid}/challengeTeam',
                json.dumps({"challengeId": self.challengeid,
                            "teamId": self.teamid})
            )


class TestChallenge:
    """Tests functions in challenge.py"""
    def setup(self):
        """Setup"""
        self.syn = mock.create_autospec(synapseclient.Synapse)
        self.challengeid = str(uuid.uuid1())
        self.teamid = str(uuid.uuid1())
        self.projectid = str(uuid.uuid1())
        self.project = synapseclient.Project(name="foo", id=self.projectid)
        self.team = synapseclient.Team(name="foo", id=self.teamid)
        self.input = Challenge(id=self.challengeid,
                               projectId=self.projectid,
                               participantTeamId=self.teamid)

    def test_get_challenge(self):
        """Tests getting challenge"""
        with patch.object(ChallengeApi, "get_challenge",
                          return_value=self.input) as patch_get:
            chal = challenge.get_challenge(self.syn, self.project)
            patch_get.assert_called_once_with(projectid=self.projectid)
            assert chal == self.input

    def test_create_challenge(self):
        """Tests create challenge object"""
        with patch.object(ChallengeApi, "create_challenge",
                          return_value=self.input) as patch_create:

            chal = challenge.create_challenge(self.syn, self.project,
                                              self.team)
            patch_create.assert_called_once_with(projectid=self.projectid,
                                                 teamid=self.teamid)
            assert chal == self.input

    def test_get_registered_challenges(self):
        """Test listing of registered challenges"""
        userprofile = Mock(ownerId=2222)
        with patch.object(self.syn, "getUserProfile",
                          return_value=userprofile) as patch_get_user,\
             patch.object(ChallengeApi, "get_registered_challenges",
                          return_value=[self.input]) as patch_get_challenges,\
             patch.object(self.syn, "get",
                          return_value=self.project) as patch_get:
            projects = challenge.get_registered_challenges(self.syn)
            assert list(projects) == [self.project]
            patch_get_user.assert_called_once()
            patch_get_challenges.assert_called_once_with(participantId=2222)
            patch_get.assert_called_once_with(self.projectid)
