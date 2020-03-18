"""
Manage Synapse connection

When writing tests use this function

@pytest.fixture(autouse=True)
def syn_connection(monkeypatch):
    '''Set _synapse_client to be SYN for all tests.'''
    monkeypatch.setattr(Synapse, "_synapse_client", SYN)

"""
import logging

import synapseclient
from synapseclient.exceptions import SynapseAuthenticationError

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class Synapse:
    """Define Synapse class"""
    _synapse_client = None

    @classmethod
    def client(cls, syn_user=None, syn_pass=None, *args, **kwargs):
        """Gets a logged in instance of the synapseclient.

        Args:
            syn_user: Synapse username
            syn_pass: Synpase password

        Returns:
            logged in synapse client
        """
        if not cls._synapse_client:
            LOGGER.debug("Getting a new Synapse client.")
            cls._synapse_client = synapseclient.Synapse(*args, **kwargs)
            try:
                cls._synapse_client.login(silent=True)
            except SynapseAuthenticationError:
                cls._synapse_client.login(syn_user, syn_pass, silent=True)

        LOGGER.debug("Already have a Synapse client, returning it.")
        return cls._synapse_client

    @classmethod
    def reset(cls):
        """Change synapse connection"""
        cls._synapse_client = None
