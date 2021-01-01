"""Testing team module"""
from unittest import mock
from unittest.mock import Mock, patch

import synapseclient
from challengeutils import teams


class TestTeam:
    """Test team module functions"""

    def setup_method(self):
        """Method called once per method"""
        self.syn = mock.create_autospec(synapseclient.Synapse)
        self.return_count = {"count": 3}

    def test__get_team_count_rest(self):
        """Test rest call wrapper"""
        with patch.object(self.syn, "restGET",
                          return_value=self.return_count) as rest_get:
            count = teams._get_team_count(self.syn, 2222)
            rest_get.assert_called_once_with("/teamMembers/count/2222")
            assert count == self.return_count

    def test_get_team_count(self):
        """Test getting team count"""
        fake_team = Mock(id=2222)
        with patch.object(self.syn, "getTeam",
                          return_value=fake_team) as get_team,\
             patch.object(teams, "_get_team_count",
                          return_value=self.return_count) as get_count:
            count = teams.get_team_count(self.syn, "team")

            get_team.assert_called_once_with("team")
            get_count.assert_called_once_with(self.syn, 2222)
            assert count == self.return_count['count']

    def test_remove_team_member(self):
        team = synapseclient.Team(id=123)
        user = synapseclient.UserProfile(ownerId=2222)

        with patch.object(self.syn, "restDELETE") as patch_rest:
            teams.remove_team_member(self.syn, team, user)
            patch_rest.assert_called_once_with(
                "/team/123/member/2222"
            )


class TestTeamDiff:
    """Test team diff"""

    def setup_method(self):
        """Method called once per method"""
        self.member1 = teams.NewUserProfile(
            ownerId='1234', firstName='test', lastName='foo', userName='temp'
        )
        self.member2 = teams.NewUserProfile(ownerId='2345')
        self.member3 = teams.NewUserProfile(ownerId='3456')
        self.member4 = teams.NewUserProfile(ownerId='4567')
        self.member5 = teams.NewUserProfile(ownerId='4444')
        self.member6 = teams.NewUserProfile(ownerId='5555')

        self.members1 = [{'member': self.member1},
                         {'member': self.member2},
                         {'member': self.member3},
                         {'member': self.member4}]
        self.members2 = [{'member': self.member1},
                         {'member': self.member2},
                         {'member': self.member5},
                         {'member': self.member6}]

        self.syn = mock.create_autospec(synapseclient.Synapse)
        self.syn.getTeamMembers.side_effect = [self.members1, self.members2]

    def test__get_team_set(self):
        """Test getting unique team members"""
        with mock.patch.object(self.syn, "getTeamMembers",
                               return_value=self.members1) as patch_get:
            members_set = teams._get_team_set(self.syn, 1)
            assert members_set == set([self.member1, self.member2,
                                       self.member3, self.member4])
            patch_get.assert_called_once_with(1)

    def test_team_members_diff(self):
        """Test getting member differences between two teams"""
        assert teams.team_members_diff(self.syn, 1, 2) == set([self.member4,
                                                               self.member3])

    def test_team_members_intersection(self):
        """Test getting member intersection between two teams"""
        assert teams.team_members_intersection(self.syn, 1, 2) == set(
            [self.member1, self.member2]
        )

    def test_team_members_union(self):
        """Test getting member union between two teams"""
        assert teams.team_members_union(self.syn, 1, 2) == set(
            [self.member1, self.member2, self.member3, self.member4,
             self.member5, self.member6]
        )
