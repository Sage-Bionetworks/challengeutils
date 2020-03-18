"""This is the baseclass for what happens to a submission"""
from abc import ABCMeta, abstractmethod
import logging
import os
from challengeutils.utils import update_single_submission_status

logging.basicConfig(format='%(asctime)s %(message)s')
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


def _remove_cached_submission(submission_file):
    """
    Remove submission file if cache clearing is requested

    Args:
        submission_file: Input submission
    """
    try:
        os.unlink(submission_file)
    except TypeError:
        pass


def get_admin(syn, admin):
    """Set admin user id to be person running the evaluation queue helper"""
    admin = admin if admin is not None else [syn.getUserProfile()['ownerId']]
    return admin


def _get_submission_submitter(syn, submission):
    """Get submitter id and name from a submission object"""
    submitterid = submission.get("teamId")
    if submitterid is not None:
        submitter_name = syn.getTeam(submitterid)['name']
    else:
        submitterid = submission.userId
        submitter_name = syn.getUserProfile(submitterid)['userName']
    return {'submitterid': submitterid,
            'submitter_name': submitter_name}


class EvaluationQueueProcessor(metaclass=ABCMeta):
    """Processor for submissions that are submitted to evaluation queues

    Attributes:
        syn: Synapse object
        evaluation: synapseclient.Evaluation object
        admin_user_ids: List of Synapse user ids.  Default is the Synapse user
            running the processor.
        dry_run: Do not update Synapse. Default is False.
        remove_cache: Removes submission file from cache. Default is False.
    """
    # Status of submissions to process
    _status = "RECEIVED"
    # Successful submissions will be placed in this status
    _success_status = None

    def __init__(self, syn, evaluation, admin_user_ids=None, dry_run=False,
                 remove_cache=False, send_messages=False,
                 notifications=True, **kwargs):
        """Init EvaluationQueueProcessor

        Args:
            syn: Synapse object
            evaluation: synapseclient.Evaluation object
            dry_run: Do not update Synapse. Default is False.
            admin_user_ids: List of Synapse user ids.  Default is the Synapse
                            user running the processor.
            remove_cache: Removes submission file from cache.
                          Default is False.
            send_messages: Send messages to submitters.
                           Default is False
            notifications: Send messages to admins
                           Default is True
        """
        self.syn = syn
        self.evaluation = syn.getEvaluation(evaluation)
        self.admin_user_ids = get_admin(syn, admin_user_ids)
        self.dry_run = dry_run
        self.remove_cache = remove_cache
        self.send_messages = send_messages
        self.notifications = notifications
        self.kwargs = kwargs

    def __call__(self):
        """
        Submission pipeline
        - Get submissions
        - Interact with the submission
        - Store the submission status
        - Notify submitter or admin about submission status
        """
        LOGGER.info("-" * 20)
        LOGGER.info(f"Evaluating {self.evaluation.name} "
                    f"({self.evaluation.id})")
        submission_bundles = self.syn.getSubmissionBundles(self.evaluation,
                                                           status=self._status)
        for submission, sub_status in submission_bundles:
            LOGGER.info(f"Interacting with submission: {submission.id}")
            # refetch the submission so that we get the file path
            # to be later replaced by a "downloadFiles" flag on
            # getSubmissionBundles
            submission_info = self.interact_with_submission(submission)

            self.store_submission_status(sub_status, submission_info)

            # Remove submission file if cache clearing is requested.
            if self.remove_cache:
                _remove_cached_submission(submission.filePath)

            # Notify submitter
            if not self.dry_run:
                self.notify(submission, submission_info)

        LOGGER.info("-" * 20)

    @abstractmethod
    def interaction_func(self, submission, **kwargs):
        """Do one thing with submission"""
        pass

    def interact_with_submission(self, submission):
        """
        Interact with submission function

        Args:
            submission: synapse Submission object

        Returns:
            dict: {'valid': True,
                   'error': None,
                   'annotations': {},
                   'message': 'Success!'}
        """
        # raise NotImplementedError
        submission = self.syn.getSubmission(submission)
        try:
            interaction_status = self.interaction_func(submission,
                                                       **self.kwargs)
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
            # TODO: allow for annotations to be added even if error
            annotations = {}
            validation_error = ex1
            validation_message = str(ex1)

        submission_info = {'valid': is_valid,
                           'error': validation_error,
                           'annotations': annotations,
                           'message': validation_message}
        return submission_info

    def store_submission_status(self, sub_status, submission_info):
        """Store submission status

        Args:
            sub_status: Synapse Submission Status
            submission_info: dict returned by interact_with_submission
        """
        annotations = submission_info['annotations']
        sub_status = update_single_submission_status(sub_status,
                                                     annotations,
                                                     is_private=False)
        is_valid = submission_info['valid']
        sub_status.status = self._success_status if is_valid else "INVALID"

        if not self.dry_run:
            sub_status = self.syn.store(sub_status)
        else:
            LOGGER.debug(sub_status)

    @abstractmethod
    def notify(self, submission, submission_info):
        """Notify submitter or admin"""
        pass
