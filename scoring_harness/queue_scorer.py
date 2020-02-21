"""This is the baseclass for what happens to a submission"""
import logging
from .base_processor import EvaluationQueueProcessor
from . import messages

logging.basicConfig(format='%(asctime)s %(message)s')
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


class EvaluationQueueScorer(EvaluationQueueProcessor):
    _status = "VALIDATED"
    _success_status = "SCORED"

    def __init__(self, syn, evaluation, admin_user_ids=None, dry_run=False,
                 remove_cache=False, send_messages=False, **kwargs):
        EvaluationQueueProcessor.__init__(self, syn, evaluation,
                                          admin_user_ids=admin_user_ids,
                                          dry_run=dry_run,
                                          remove_cache=remove_cache, **kwargs)
        self.send_messages = send_messages

    def interaction_func(self, submission, **kwargs):
        raise NotImplementedError

    def notify(self, submission, submission_info):
        """Notify submitter or admin"""
        # send message AFTER storing status to ensure
        # we don't get repeat messages
        is_valid = submission_info['valid']
        message = submission_info['message']
        # we don't get repeat messages
        profile = self.syn.getUserProfile(submission.userId)
        if is_valid:
            messages.scoring_succeeded(syn=self.syn,
                                       userids=[submission.userId],
                                       send_messages=self.send_messages,
                                       dry_run=self.dry_run,
                                       message=message,
                                       username=profile.userName,
                                       queue_name=self.evaluation.name,
                                       submission_name=submission.name,
                                       submission_id=submission.id,
                                       challenge_synid=self.evaluation.contentSource)
        else:
            messages.scoring_error(syn=self.syn,
                                   userids=self.admin_user_ids,
                                   send_messages=self.send_messages,
                                   dry_run=self.dry_run,
                                   message=message,
                                   username="Challenge Administrator",
                                   queue_name=self.evaluation.name,
                                   submission_name=submission.name,
                                   submission_id=submission.id,
                                   challenge_synid=self.evaluation.contentSource)
