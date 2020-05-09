"""Test challeng service"""
from challengeutils.synapseservices.challenge import Challenge


def test_challenge_obj():
    """Tests that a challenge object can be instantiated"""
    challenge_dict = {'id': 'challenge_1',
                      'projectId': 'project_1',
                      'participantTeamId': 'team_1',
                      'etag': 'etag_1'}
    challenge_obj = Challenge(**challenge_dict)
    assert challenge_obj.to_dict() == challenge_dict
