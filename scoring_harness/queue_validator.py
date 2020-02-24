"""This is the baseclass for what happens to a submission"""
import logging
from .base_processor import EvaluationQueueProcessor
from .base_processor import _get_submission_submitter
from . import messages

logging.basicConfig(format='%(asctime)s %(message)s')
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


class EvaluationQueueValidator(EvaluationQueueProcessor):
    _success_status = "VALIDATED"
    # This acknowledge receipt is here specifically for submission validation
    # We may not want to return validation success emails
    # Set this to true in the template class if you want success emails
    # returned
    acknowledge_receipt = False

    def interaction_func(self, submission, **kwargs):
        raise NotImplementedError

    def notify(self, submission, submission_info):
        """Notify submitter or admin"""
        # send message AFTER storing status to ensure
        # we don't get repeat messages
        is_valid = submission_info['valid']
        error = submission_info['error']
        message = submission_info['message']

        submitter_info = _get_submission_submitter(self.syn, submission)
        submitterid_list = [submitter_info['submitterid']]
        submitter_name = submitter_info['submitter_name']
        if is_valid:
            messages.validation_passed(syn=self.syn,
                                       userids=submitterid_list,
                                       acknowledge_receipt=self.acknowledge_receipt,  # noqa pylint: disable=line-too-long
                                       dry_run=self.dry_run,
                                       username=submitter_name,
                                       queue_name=self.evaluation.name,
                                       submission_id=submission.id,
                                       submission_name=submission.name,
                                       challenge_synid=self.evaluation.contentSource)  # noqa pylint: disable=line-too-long
        else:
            if not isinstance(error, AssertionError):
                submitterid_list = self.admin_user_ids
                submitter_name = "Challenge Administrator"
            messages.validation_failed(syn=self.syn,
                                       userids=submitterid_list,
                                       send_messages=self.send_messages,
                                       dry_run=self.dry_run,
                                       username=submitter_name,
                                       queue_name=self.evaluation.name,
                                       submission_id=submission.id,
                                       submission_name=submission.name,
                                       message=message,
                                       challenge_synid=self.evaluation.contentSource)  # noqa pylint: disable=line-too-long
