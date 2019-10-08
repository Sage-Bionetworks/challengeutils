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
                 remove_cache=False, **kwargs):
        EvaluationQueueProcessor.__init__(self, syn, evaluation,
                                          admin_user_ids=None, dry_run=False,
                                          remove_cache=False, **kwargs)

    def interaction_func(self, submission, **kwargs):
        goldstandard = kwargs.get("goldstandard")
        LOGGER.info(goldstandard)
        auc = 4
        bac = 3
        score = 1
        score_dict = dict(auc=round(auc, 4), bac=bac, score=score)
        message = f"Your submission ({submission.name}) has been scored!"
        score_status = {'valid': True,
                        'annotations': score_dict,
                        'message': message}
        return score_status

    def notify(self, submission, submission_info, **kwargs):
        """Notify submitter or admin"""
        # send message AFTER storing status to ensure
        # we don't get repeat messages
        is_valid = submission_info['valid']
        message = submission_info['message']
        send_messages = kwargs.get("send_messages")
        # we don't get repeat messages
        profile = self.syn.getUserProfile(submission.userId)
        if is_valid:
            messages.scoring_succeeded(syn=self.syn,
                                       userids=[submission.userId],
                                       send_messages=send_messages,
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
                                   send_messages=send_messages,
                                   dry_run=self.dry_run,
                                   message=message,
                                   username="Challenge Administrator,",
                                   queue_name=self.evaluation.name,
                                   submission_name=submission.name,
                                   submission_id=submission.id,
                                   challenge_synid=self.evaluation.contentSource)
