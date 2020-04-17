"""Tests challenge services"""
import pytest
import mock
from mock import patch

import synapseclient

from challengeutils.synapseservices.challenge import Challenge
from challengeutils.challenge import ChallengeApi


def test_challenge():
    """Tests that a challenge object can be instantiated"""
    challenge_dict = {'id': 'challenge_1',
                      'projectId': 'project_1',
                      'participantTeamId': 'team_1',
                      'etag': 'etag_1'}
    challenge_obj = Challenge(**challenge_dict)
    assert challenge_obj.to_dict() == challenge_dict


class TestChallengeApi:

    def setup(self):
        self.syn = mock.create_autospec(synapseclient.Synapse)
        self.challengeid = "challenge1"
        self.teamid = "team1"
        self.projectid = "project1"
        self.challenge_dict = {'id': self.challengeid,
                               'participantTeamId': self.teamid,
                               'projectId': self.projectid}
        self.challenge_api = ChallengeApi(self.syn, id=self.challengeid,
                                          projectId=self.projectid,
                                          participantTeamId=self.teamid)
        self.expected = Challenge(id=self.challengeid,
                                  projectId=self.projectid,
                                  participantTeamId=self.teamid,
                                  etag=None)

        self.null_api = ChallengeApi(self.syn)

        self.noid_api = ChallengeApi(self.syn, projectId=self.projectid,
                                     participantTeamId=self.teamid)

    def test_init(self):
        """Test Challenge obj init"""
        challenge = self.challenge_api._challenge
        assert challenge == Challenge(id=self.challengeid,
                                      projectId=self.projectid,
                                      participantTeamId=self.teamid)

    def test_create_challenge(self):
        """Tests that a challenge object can be instantiated"""
        challenge = self.challenge_api._challenge
        with patch.object(self.syn, "restPOST",
                          return_value=self.challenge_dict) as patch_restpost:
            challenge_obj = self.challenge_api.create_challenge()
            assert challenge_obj == self.expected
            patch_restpost.assert_called_once_with('/challenge',
                                                   str(challenge))

    def test_get_challenge__with_project(self):
        """Tests getting challenge with project id"""
        with patch.object(self.syn, "restGET",
                          return_value=self.challenge_dict) as patch_restget:
            challenge_obj = self.noid_api.get_challenge()
            assert challenge_obj == self.expected
            patch_restget.assert_called_once_with(
                f"/entity/{self.projectid}/challenge"
            )

    def test_get_challenge__with_id(self):
        """Tests getting challenge with challenge id"""
        with patch.object(self.syn, "restGET",
                          return_value=self.challenge_dict) as patch_restget:
            challenge_obj = self.challenge_api.get_challenge()
            assert challenge_obj == self.expected
            patch_restget.assert_called_once_with(
                f"/challenge/{self.challengeid}"
            )

    def test_get_challenge__raise_error(self):
        """If challenge and project id is missing, raise error"""
        with pytest.raises(ValueError,
                           match="Must pass in `id` or `projectId`"):
            self.null_api.get_challenge()

    def test_update_challenge(self):
        challenge = self.challenge_api._challenge
        with patch.object(self.syn, "restPUT",
                          return_value=self.challenge_dict) as patch_restput:
            challenge_obj = self.challenge_api.update_challenge()
            assert challenge_obj == self.expected
            patch_restput.assert_called_once_with(f'/challenge/{self.challengeid}',
                                                  str(challenge))

    def test_update_challenge__raise_error(self):
        with pytest.raises(ValueError,
                           match="Must pass in `id`"):
            self.noid_api.update_challenge()

    def test_delete_challenge(self):
        challenge = self.challenge_api._challenge
        with patch.object(self.syn, "restDELETE") as patch_restdelete:
            self.challenge_api.delete_challenge()
            patch_restdelete.assert_called_once_with(
                f'/challenge/{self.challengeid}'
            )

    def test_delete_challenge__raise_error(self):
        with pytest.raises(ValueError,
                           match="Must pass in `id`"):
            self.noid_api.delete_challenge()

    def test_get_registered_participants(self):
        with patch.object(self.syn, "restGET")  as patch_restget:
            self.challenge_api.get_registered_participants()
            patch_restget.assert_called_once_with(
                f'/challenge/{self.challengeid}/participant'
            )

    def test_get_registered_participants__raise_error(self):
        with pytest.raises(ValueError,
                           match="Must pass in `id`"):
            self.noid_api.get_registered_participants()

    def test_get_registered_teams(self):
        with patch.object(self.syn, "restGET") as patch_restget:
            self.challenge_api.get_registered_teams()
            patch_restget.assert_called_once_with(
                f'/challenge/{self.challengeid}/challengeTeam'
            )

    def test_get_registered_teams__raise_error(self):
        with pytest.raises(ValueError,
                           match="Must pass in `id`"):
            self.noid_api.get_registered_teams()