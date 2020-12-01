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
