from dataclasses import dataclass


@dataclass
class Challenge:
    """Challenge - Settings for a Challenge Project

    Args:
        id: The ID of this Challenge object
        etag: Synapse employs an Optimistic Concurrency Control (OCC) scheme to handle concurrent updates.
        projectId: The ID of the Project the challenge is used with.
        participantTeamId: The ID of the Team which users join to participate in the Challenge
    """
    id: str = None
    projectId: str = None
    etag: str = None
    participantTeamId: str = None
