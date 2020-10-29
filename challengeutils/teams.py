"""Team related functions"""
from synapseclient.core.utils import id_of


def _get_team_count(syn, teamid):
    """Get number of team members

    Args:
        syn: Synapse object
        team: Synapse team id
    """
    count = syn.restGET(f"/teamMembers/count/{teamid}")
    return count


def get_team_count(syn, team):
    """Get number of team members

    Args:
        syn: Synapse object
        team: synaspeclient.Team or its id
    """
    team_obj = syn.getTeam(team)
    count = _get_team_count(syn, team_obj.id)
    return count['count']
