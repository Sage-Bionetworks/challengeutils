import pytest
import mock
import challengeutils
import synapseclient

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

def test__get_team_set():
    with mock.patch.object(syn, "getTeamMembers", return_value=members1) as patch_syn_get_team_members:
        members_set = challengeutils.utils._get_team_set(syn, 1)
        assert members_set == set(['1234','2345','3456','4567'])
        patch_syn_get_team_members.assert_called_once_with(1)

def test_team_members_diff():
    assert challengeutils.utils.team_members_diff(syn, 1, 2) == set(['4567','3456'])

def test_team_members_intersection():
    assert challengeutils.utils.team_members_intersection(syn, 1, 2) == set(['1234','2345'])

def test_team_members_union():
    assert challengeutils.utils.team_members_union(syn, 1, 2) == set(['1234','2345','3456','4567','5555','4444'])
