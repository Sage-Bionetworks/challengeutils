"""This is the baseclass for what happens to a submission"""
import logging
from .base_processor import EvaluationQueueProcessor
from .base_processor import _get_submission_submitter
from . import messages

logging.basicConfig(format='%(asctime)s %(message)s')
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


class EvaluationQueueScorer(EvaluationQueueProcessor):
    _status = "VALIDATED"
    _success_status = "SCORED"

    def interaction_func(self, submission, **kwargs):
        raise NotImplementedError

    def notify(self, submission, submission_info):
        """Notify submitter or admin"""
        # send message AFTER storing status to ensure
        # we don't get repeat messages
        is_valid = submission_info['valid']
        message = submission_info['message']

        submitter_info = _get_submission_submitter(self.syn, submission)
        submitterid = submitter_info['submitterid']
        submitter_name = submitter_info['submitter_name']
        if is_valid:
            messages.scoring_succeeded(syn=self.syn,
                                       userids=[submitterid],
                                       send_messages=self.send_messages,
                                       dry_run=self.dry_run,
                                       message=message,
                                       username=submitter_name,
                                       queue_name=self.evaluation.name,
                                       submission_name=submission.name,
                                       submission_id=submission.id,
                                       challenge_synid=self.evaluation.contentSource)  # noqa pylint: disable=line-too-long
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
                                   challenge_synid=self.evaluation.contentSource)  # noqa pylint: disable=line-too-long
