'''
Manage Synapse connection
'''
import synapseclient
import logging
logging.basicConfig(logging.DEBUG)
LOGGER = logging.getLogger(__name__)


class Synapse:
    '''
    Define Synapse class
    '''
    _synapse_client = None
    def __init__(self, syn_user, syn_pass):
        self.syn_user = syn_user
        self.syn_pass = syn_pass

    @classmethod
    def client(cls, *args, **kwargs):
        """
        Gets a logged in instance of the synapseclient.
        """
        if not cls._synapse_client:
            LOGGER.debug("Getting a new Synapse client.")
            cls._synapse_client = synapseclient.Synapse(*args, **kwargs)
            try:
                cls._synapse_client.login(silent=True)
            except:
                cls._synapse_client.login(self.syn_user, self.syn_pass,
                                          silent=True)

        LOGGER.debug("Already have a Synapse client, returning it.")
        return cls._synapse_client
