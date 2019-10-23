"""Challenge configuration"""
from scoring_harness.queue_validator import EvaluationQueueValidator
from scoring_harness.queue_scorer import EvaluationQueueScorer

class Validate(EvaluationQueueValidator):

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

EVALUATION_QUEUES_CONFIG = [
    {
        'id': 1,
        'scoring_func': Score,
        'validation_func': Validate,
        'goldstandard_path': 'path/to/sc1gold.txt'
    },
    {
        'id': 2,
        'scoring_func': Score,
        'validation_func': Validate,
        'goldstandard_path': 'path/to/sc2gold.txt'
    }
]