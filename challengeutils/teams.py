"""Team related functions"""
from typing import Union

from synapseclient import Synapse, Team
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
