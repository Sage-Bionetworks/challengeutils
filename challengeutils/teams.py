"""Team related functions"""
from typing import Union

from synapseclient import Synapse, Team, UserProfile
from synapseclient.core.utils import id_of


def _get_team_count(syn: Synapse, teamid: int) -> dict:
    """Rest call wrapper for getting team member count

    Args:
        syn: Synapse object
        teamid: Synapse team id
    """
    count = syn.restGET(f"/teamMembers/count/{teamid}")
    return count


def get_team_count(syn: Synapse, team: Union[int, str, Team]) -> int:
    """Get number of team members

    Args:
        syn: Synapse object
        team: synaspeclient.Team, its id, or name.
    """
    team_obj = syn.getTeam(team)
    count = _get_team_count(syn, team_obj.id)
    return count['count']


def remove_team_member(syn, team, user):
    """Removes team member

    Args:
        syn: Synapse object
        team: synaspeclient.Team or its id
        user: synapseclient.UserProfile or its id
    """
    teamid = id_of(team)
    userid = id_of(user)
    syn.restDELETE(f"/team/{teamid}/member/{userid}")


class NewUserProfile(UserProfile):
    '''
    Create new user profile that makes Userprofiles hashable
    SYNPY-879
    '''
    def __hash__(self):
        return int(self['ownerId'])


def _get_team_set(syn, team):
    '''
    Helper function to return a set of usernames

    Args:
        syn: Synapse object
        team: Synapse team id, name or object

    Returns:
        Set of synapse user profiles in team
    '''
    members = syn.getTeamMembers(team)
    members_set = set(NewUserProfile(**member['member']) for member in members)
    return members_set


def team_members_diff(syn, a, b):
    '''
    Calculates the diff between teama and teamb

    Args:
        syn: Synapse object
        a: Synapse Team id or name
        b: Synapse Team id or name

    Returns:
        Set of synapse user profiles in teama but not in teamb
    '''
    uniq_teama_members = _get_team_set(syn, a)
    uniq_teamb_members = _get_team_set(syn, b)
    members_not_in_teamb = uniq_teama_members.difference(uniq_teamb_members)
    return members_not_in_teamb


def team_members_intersection(syn, a, b):
    '''
    Calculates the intersection between teama and teamb

    Args:
        syn: Synapse object
        a: Synapse Team id or name
        b: Synapse Team id or name

    Returns:
        Set of synapse user profiles that belong in both teams
    '''
    uniq_teama_members = _get_team_set(syn, a)
    uniq_teamb_members = _get_team_set(syn, b)
    intersect_members = uniq_teama_members.intersection(uniq_teamb_members)
    return intersect_members


def team_members_union(syn, a, b):
    '''
    Calculates the union between teama and teamb

    Args:
        syn: Synapse object
        a: Synapse Team id or name
        b: Synapse Team id or name

    Returns:
        Set of a combination of synapse user profiles from both teams
    '''
    uniq_teama_members = _get_team_set(syn, a)
    uniq_teamb_members = _get_team_set(syn, b)
    union_members = uniq_teama_members.union(uniq_teamb_members)
    return union_members
