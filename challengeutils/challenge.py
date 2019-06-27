import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Challenge(object):
    def __init__(self, syn):
        self.syn = syn
