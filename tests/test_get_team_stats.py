import pytest
import mock
import challengeutils
import synapseclient


def test_get_team_set():
    syn = mock.create_autospec(synapseclient.Synapse) 
    with mock.patch.object(syn, "getTeamMembers", return_value=[]) as patch_syn_get_team_members:
        members_set = challengeutils.utils._get_team_set(syn, 1)
        assert members_set == set()
        patch_syn_get_team_members.assert_called_once_with(1)


def test_team_members_diff():
    members1 = [{'member': {'ownerId': '1234'}},
               {'member': {'ownerId': '2345'}},
               {'member': {'ownerId': '3456'}},
               {'member': {'ownerId': '4567'}}]
    members2 = [{'member': {'ownerId': '1234'}},
               {'member': {'ownerId': '2345'}},
               {'member': {'ownerId': '4444'}},
               {'member': {'ownerId': '5555'}}]
    team_member_map = {
    (1,) : members1,
    (2,) : members2
    }   
    def get_team_member_results(*args):
        return(team_member_map[args])

    syn = mock.create_autospec(synapseclient.Synapse) 
    syn.getTeamMembers.side_effect = get_team_member_results

    assert challengeutils.utils.team_members_diff(syn, 1, 2) == set(['4567','3456'])
