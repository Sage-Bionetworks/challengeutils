# -----------------------------------------------------------------------------
#
# challenge specific code and configuration
#
# -----------------------------------------------------------------------------
# Use rpy2 if you have R scoring functions
# import rpy2.robjects as robjects
# import os
# filePath = os.path.join(
#     os.path.dirname(os.path.abspath(__file__)), 'getROC.R')
# robjects.r("source('%s')" % filePath)
# AUC_pAUC = robjects.r('GetScores')

# Configuring them here as a list will save a round-trip to the server
# every time the script starts and you can link the challenge queues to
# the correct scoring/validation functions.
# Predictions will be validated and scored


def validate_func(submission_path, goldstandard_path):
    '''
    Validate submission.

    MUST USE ASSERTION ERRORS!!!

    eg.
    >>> assert os.path.basename(submission_path) == "prediction.tsv", \
    >>> "Submission file must be named prediction.tsv"
    or raise AssertionError()...
    Only assertion errors will be returned to participants,
    all other errors will be returned to the admin

    Args:
        submission_path:  Path to submission file
        goldstandard_path: Path to truth file

    Returns:
        Must return a boolean and validation message
    '''
    is_valid = True
    message = "Passed Validation"
    return(is_valid, message)


def score1(submission_path, goldstandard_path):
    '''
    Scoring function number 1

    Args:
        submission_path:  Path to submission file
        goldstandard_path: Path to truth file

    Returns:
        Must return score dictionary and a scoring message
    '''
    score1 = 4
    score2 = 3
    score3 = 2
    score_dict = dict(score=round(score1, 4), rmse=score2, auc=score3)
    message = "Your submission has been scored!"
    return(score_dict, message)


def score2(submission_path, goldstandard_path):
    '''
    Scoring function number 2

    Args:
        submission_path:  Path to submission file
        goldstandard_path: Path to truth file

    Returns:
        Must return score dictionary and a scoring message
    '''
    # Score against goldstandard
    score1 = 2
    score2 = 3
    score3 = 5
    score_dict = dict(score=round(score1, 4), rmse=score2, auc=score3)
    message = "Your submission has been scored!"
    return(score_dict, message)


EVALUATION_QUEUES_CONFIG = [
    {
        'id': 1,
        'scoring_func': score1,
        'validation_func': validate_func,
        'goldstandard_path': 'path/to/sc1gold.txt'
    },
    {
       'id': 2,
       'scoring_func': score2,
       'validation_func': validate_func,
       'goldstandard_path': 'path/to/sc2gold.txt'
    }
]
