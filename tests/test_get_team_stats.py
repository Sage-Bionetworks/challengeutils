from unittest import mock

import synapseclient

import challengeutils.utils


member1 = challengeutils.utils.NewUserProfile(
    ownerId='1234', firstName='test', lastName='foo', userName='temp')
member2 = challengeutils.utils.NewUserProfile(ownerId='2345')
member3 = challengeutils.utils.NewUserProfile(ownerId='3456')
member4 = challengeutils.utils.NewUserProfile(ownerId='4567')
member5 = challengeutils.utils.NewUserProfile(ownerId='4444')
member6 = challengeutils.utils.NewUserProfile(ownerId='5555')

members1 = [{'member': member1},
            {'member': member2},
            {'member': member3},
            {'member': member4}]
members2 = [{'member': member1},
            {'member': member2},
            {'member': member5},
            {'member': member6}]
team_member_map = {
    (1,): members1,
    (2,): members2}


def get_team_member_results(*args):
    return(team_member_map[args])


syn = mock.create_autospec(synapseclient.Synapse)
syn.getTeamMembers.side_effect = get_team_member_results


def test__get_team_set():
    with mock.patch.object(syn, "getTeamMembers", return_value=members1)\
         as patch_syn_get_team_members:
        members_set = challengeutils.utils._get_team_set(syn, 1)
        assert members_set == set([member1, member2, member3, member4])
        patch_syn_get_team_members.assert_called_once_with(1)


def test_team_members_diff():
    assert challengeutils.utils.team_members_diff(syn, 1, 2) == \
        set([member4, member3])


def test_team_members_intersection():
    assert challengeutils.utils.team_members_intersection(syn, 1, 2) == \
        set([member1, member2])


def test_team_members_union():
    assert challengeutils.utils.team_members_union(syn, 1, 2) == \
        set([member1, member2, member3, member4, member5, member6])
