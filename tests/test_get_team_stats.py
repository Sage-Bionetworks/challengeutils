"""Test get team stats"""
import mock

import synapseclient

import challengeutils.utils
from challengeutils.synapse import Synapse

MEMBER1 = challengeutils.utils.NewUserProfile(ownerId='1234',
                                              firstName='test',
                                              lastName='foo',
                                              userName='temp')
MEMBER2 = challengeutils.utils.NewUserProfile(ownerId='2345')
MEMBER3 = challengeutils.utils.NewUserProfile(ownerId='3456')
MEMBER4 = challengeutils.utils.NewUserProfile(ownerId='4567')
MEMBER5 = challengeutils.utils.NewUserProfile(ownerId='4444')
MEMBER6 = challengeutils.utils.NewUserProfile(ownerId='5555')

MEMBERS1 = [{'member': MEMBER1},
            {'member': MEMBER2},
            {'member': MEMBER3},
            {'member': MEMBER4}]
MEMBERS2 = [{'member': MEMBER1},
            {'member': MEMBER2},
            {'member': MEMBER5},
            {'member': MEMBER6}]
TEAM_MEMBER_MAP = {(1,): MEMBERS1,
                   (2,): MEMBERS2}


def get_team_member_results(*args):
    return TEAM_MEMBER_MAP[args]

SYN = mock.create_autospec(synapseclient.Synapse)
Synapse._synapse_client = SYN
SYN.getTeamMembers.side_effect = get_team_member_results


def test__get_team_set():
    with mock.patch.object(SYN, "getTeamMembers",
                           return_value=MEMBERS1) as patch_syn_get_members:
        members_set = challengeutils.utils._get_team_set(1)
        assert members_set == set([MEMBER1, MEMBER2, MEMBER3, MEMBER4])
        patch_syn_get_members.assert_called_once_with(1)


def test_team_members_diff():
    assert challengeutils.utils.team_members_diff(1, 2) == \
        set([MEMBER4, MEMBER3])


def test_team_members_intersection():
    assert challengeutils.utils.team_members_intersection(1, 2) == \
        set([MEMBER1, MEMBER2])


def test_team_members_union():
    assert challengeutils.utils.team_members_union(1, 2) == \
        set([MEMBER1, MEMBER2, MEMBER3, MEMBER4, MEMBER5, MEMBER6])
