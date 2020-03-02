"""Challenge Services"""
from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Challenge:
    """Challenge - Settings for a Challenge Project

    Args:
        id: The ID of this Challenge object
        etag: Synapse employs an Optimistic Concurrency Control (OCC)
              scheme to handle concurrent updates.
        projectId: The ID of the Project the challenge is used with.
        participantTeamId: The ID of the Team which users join to participate
                           in the Challenge
    """
    id: str = None
    projectId: str = None
    etag: str = None
    participantTeamId: str = None

    @staticmethod
    def post_uri():
        """Creates a challenge"""
        return '/challenge'

    def get_uri(self):
        """Gets a challenge"""
        if self.id is not None:
            return f'/challenge/{self.id}'
        if self.projectId is not None:
            return f'/entity/{self.projectId}/challenge'
        raise ValueError("Must pass in challenge id or Synapse project id")

    def put_uri(self):
        """Updates a challenge"""
        return f'/challenge/{self.id}'

    def delete_uri(self):
        """Deletes a challenge"""
        return f'/challenge/{self.id}'

    def get_participants_uri(self):
        """Lists participants registered for a challenge"""
        return f'/challenge/{self.id}/participant'

    def get_teams_registered_uri(self):
        """Lists teams registered for a challenge"""
        return f'/challenge/{self.id}/challengeTeam'
