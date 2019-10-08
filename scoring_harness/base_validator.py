"""This is the baseclass for what happens to a submission"""
import logging
from .base_processor import EvaluationQueueProcessor
from . import messages

logging.basicConfig(format='%(asctime)s %(message)s')
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


class EvaluationQueueValidator(EvaluationQueueProcessor):
    _success_status = "VALIDATED"

    def __init__(self, syn, evaluation, admin_user_ids=None, dry_run=False,
                 remove_cache=False, **kwargs):
        EvaluationQueueProcessor.__init__(self, syn, evaluation,
                                          admin_user_ids=None, dry_run=False,
                                          remove_cache=False, **kwargs)

    def interaction_func(self, submission, **kwargs):
        assert submission.filePath is not None, \
            "Submission must be a Synapse File and not Project/Folder"
        goldstandard = kwargs.get("goldstandard")
        LOGGER.info(goldstandard)
        is_valid = True
        message = "Passed Validation"
        annotations = {'round': 1}
        submission_info = {'valid': is_valid,
                           'annotations': annotations,
                           'message': message}
        return submission_info

    def notify(self, submission, submission_info, **kwargs):
        """Notify submitter or admin"""
        # send message AFTER storing status to ensure
        # we don't get repeat messages
        is_valid = submission_info['valid']
        error = submission_info['error']
        message = submission_info['message']
        send_messages = kwargs.get("send_messages")
        acknowledge_receipt = kwargs.get("acknowledge_receipt")

        profile = self.syn.getUserProfile(submission.userId)
        if is_valid:
            messages.validation_passed(syn=self.syn,
                                       userids=[submission.userId],
                                       acknowledge_receipt=acknowledge_receipt,
                                       dry_run=self.dry_run,
                                       username=profile.userName,
                                       queue_name=self.evaluation.name,
                                       submission_id=submission.id,
                                       submission_name=submission.name,
                                       challenge_synid=self.evaluation.contentSource)
        else:
            if isinstance(error, AssertionError):
                send_to = [submission.userId]
                username = profile.userName
            else:
                send_to = self.admin_user_ids
                username = "Challenge Administrator"

            messages.validation_failed(syn=self.syn,
                                       userids=send_to,
                                       send_messages=send_messages,
                                       dry_run=self.dry_run,
                                       username=username,
                                       queue_name=self.evaluation.name,
                                       submission_id=submission.id,
                                       submission_name=submission.name,
                                       message=message,
                                       challenge_synid=self.evaluation.contentSource)
