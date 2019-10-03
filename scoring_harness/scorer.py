"""This is the baseclass for what happens to a submission"""
import logging
import os
from .helper import EvaluationQueuePipeline
from . import messages

logging.basicConfig(format='%(asctime)s %(message)s')
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)



class EvaluationQueueScorer(EvaluationQueuePipeline):

    def interact_with_submission(self, submission):
        submission = self.syn.getSubmission(submission)
        try:
            if submission.filePath is None:
                submission_input = submission
            else:
                submission_input = submission.filePath
            interaction_status = self.interaction_func(submission_input,
                                                       self.goldstandard_path)
            is_valid = interaction_status['valid']
            annotations = interaction_status['annotations']
            validation_error = None
            validation_message = interaction_status['message']
        except Exception as ex1:
            LOGGER.error("Exception during validation: "
                         f"{type(ex1)} {ex1} {str(ex1)}")
            # ex1 only happens in this scope in python3,
            # so must store validation_error as a variable
            is_valid = False
            annotations = {}
            validation_error = ex1
            validation_message = str(ex1)

        submission_info = {'valid': is_valid,
                           'error': validation_error,
                           'annotations': annotations,
                           'message': validation_message}
        return submission_info


    def notify(self, submission, submission_info):
        """Notify submitter or admin"""
        # send message AFTER storing status to ensure
        # we don't get repeat messages
        is_valid = submission_info['valid']
        error = submission_info['error']
        message = submission_info['message']

        profile = self.syn.getUserProfile(submission.userId)
        if is_valid:
            messages.validation_passed(syn=self.syn,
                                       userids=[submission.userId],
                                       acknowledge_receipt=self.acknowledge_receipt,
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
                                       send_messages=self.send_messages,
                                       dry_run=self.dry_run,
                                       username=username,
                                       queue_name=self.evaluation.name,
                                       submission_id=submission.id,
                                       submission_name=submission.name,
                                       message=message,
                                       challenge_synid=self.evaluation.contentSource)
