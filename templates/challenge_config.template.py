"""Challenge configuration"""
import time

from synapseclient import Submission, Project, AUTHENTICATED_USERS
from synapseclient.exceptions import SynapseHTTPError
import synapseutils

from challengeutils import permissions
from scoring_harness.queue_validator import EvaluationQueueValidator
from scoring_harness.queue_scorer import EvaluationQueueScorer


class Validate(EvaluationQueueValidator):
    """Example Validate interaction"""
    def interaction_func(self, submission, goldstandard_path):
        assert submission.filePath is not None, \
            "Submission must be a Synapse File and not Project/Folder"
        print(goldstandard_path)
        is_valid = True
        message = "Passed Validation"
        annotations = {'round': 1}
        submission_info = {'valid': is_valid,
                           'annotations': annotations,
                           'message': message}
        return submission_info


class Score(EvaluationQueueScorer):
    """Example Score interaction"""
    def interaction_func(self, submission, goldstandard_path):
        print(goldstandard_path)
        auc = 4
        bac = 3
        score = 1
        score_dict = dict(auc=round(auc, 4), bac=bac, score=score)
        message = f"Your submission ({submission.name}) has been scored!"
        score_status = {'valid': True,
                        'annotations': score_dict,
                        'message': message}
        return score_status


class ValidateProject(EvaluationQueueValidator):
    """Template for ValidateProject submissions"""
    def interaction_func(self, submission, public=True, admin=None):
        """Validates Projects

        Args:
            submission: Submission object

            public: If the writeup needs to be public. Defaults to True
            admin: Specify Synapse userid that writeup needs to be
                   shared with
        Returns:
            validation status dict
        """

        not_writeup_error = (
            "This is the writeup submission queue - submission must be a "
            "Synapse Project.  Please submit to the subchallenge queues "
            "for prediction file submissions."
        )
        assert isinstance(submission, Submission), not_writeup_error
        assert isinstance(submission['entity'], Project), not_writeup_error
        # Replace with the challenge project id here
        assert submission.entityId != "syn1234", \
            "Writeup submission must be your project and not the challenge site"

        # Add in users to share this with
        share_with = []
        try:
            if public:
                message = f"Please make your private project ({submission['entityId']}) public"
                share_with.append(message)
                ent = self.syn.getPermissions(submission['entityId'],
                                              AUTHENTICATED_USERS)
                assert "READ" in ent and "DOWNLOAD" in ent, message
                ent = self.syn.getPermissions(submission['entityId'])
                assert "READ" in ent, message
            if admin is not None:
                message = (f"Please share your private directory ({submission['entityId']})"
                           f" with the Synapse user `{admin}` with `Can Download` permissions.")
                share_with.append(message)
                ent = self.syn.getPermissions(submission['entityId'], admin)
                assert "READ" in ent and "DOWNLOAD" in ent, message
        except SynapseHTTPError as syn_error:
            if syn_error.response.status_code == 403:
                raise AssertionError("\n".join(share_with))
            raise syn_error
        validation_status = {'valid': True,
                             'annotations': {},
                             'message': "Validated!"}
        return validation_status


class ArchiveProject(EvaluationQueueScorer):
    """Template for ArchiveProject submissions"""
    _success_status = "ACCEPTED"

    def interaction_func(self, submission, admin):
        """Archives Project Submissions

        Args:
            submission: Submission object
            admin: Specify Synapse userid/team for archive to be
                   shared with
        Returns:
            archive status dict
        """

        project_entity = Project('Archived {} {} {} {}'.format(
            submission.name.replace("&", "+").replace("'", ""),
            int(round(time.time() * 1000)),
            submission.id,
            submission.entityId))
        new_project_entity = self.syn.store(project_entity)
        permissions.set_entity_permissions(self.syn, new_project_entity,
                                           admin, "admin")

        synapseutils.copy(self.syn, submission.entityId,
                          new_project_entity.id)
        archived = {"archived": new_project_entity.id}

        archive_status = {'valid': True,
                          'annotations': archived,
                          'message': "Archived!"}
        return archive_status


EVALUATION_QUEUES_CONFIG = [
    {'id': 1,
     'func': Validate,
     'kwargs': {'goldstandard_path': 'path/to/sc1gold.txt'}},
    {'id': 1,
     'func': Score,
     'kwargs': {'goldstandard_path': 'path/to/sc1gold.txt'}},
    {'id': 2,
     'func': ValidateProject,
     'kwargs': {'public': True,
                'admin': 'foo'}},
    {'id': 2,
     'func': ArchiveProject,
     'kwargs': {'admin': 'foo'}}
]
