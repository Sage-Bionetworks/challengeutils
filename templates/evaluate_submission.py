"""Example evaluation queue configuration that is required for the command
line command:

>>> challengeutils evaluatequeue python_config json_config

This is a example of the python_config which is linked closely with
the json_config.  Create a Python class that extends QueueEvaluator.
Your class must specify `_status`, `_success_status`, and
`_evaluation_function`.  The `_evaluation_function` must return
a SubmissionInfo class which includes

valid: A boolean value, True if your submission is 'valid'
error: A Python Exception (e.g ValueError)
annotations: A dictionary containing whatever values you want to annotate
             your submission with
"""
from challengeutils.evaluation_queue import QueueEvaluator, SubmissionInfo


class ExampleEvaluator(QueueEvaluator):
    """Example evaluation of queue"""
    # Evaluates all submissions with 'RECEIVED' submission
    _status = "RECEIVED"
    # Successful evaluations will be labeled 'ACCEPTED'
    _success_status = "ACCEPTED"

    # Define whatever evaluation function you would like here
    def _evaluation_function(self, submission, **kwargs):
        """Define your evaluation function here"""
        assert submission.filePath is not None, \
            "Submission must be a Synapse File and not Project/Folder"
        annotations = {'round': 1}
        # Must return this format
        submission_info = SubmissionInfo(valid=True, annotations=annotations)
        return submission_info
