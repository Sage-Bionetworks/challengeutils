'''

Challenge specific code and configuration

'''
from synapseclient import Submission, Project, AUTHENTICATED_USERS
from synapseclient.exceptions import SynapseHTTPError
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


def no_score(submission_path, goldstandard_path):
    '''
    Use this function for evaluation queues that don't need scoring
    Args:
        submission_path:  Path to submission file
        goldstandard_path: Path to truth file
    '''
    return submission_path, goldstandard_path


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
    # Sometimes participants accidentally submit Projects/Folders
    assert not isinstance(submission_path, Submission), \
        "Submission must be a Synapse File and not Project/Folder"
    is_valid = True
    message = "Passed Validation"
    validation_annotations = {'round': 1}
    validation_status = {'valid': is_valid,
                         'annotations'': validation_annotations,
                         'message': message}
    return validation_status


def validate_writeup(submission, goldstandard_path, syn,
                     public=True, admin=None):
    '''
    Validates challenge writeup

    Args:
        submission: Submission object
        goldstandard_path: Unused
        syn: Synapse object
        public: If the writeup needs to be public. Defaults to True
        admin: Specify Synapse userid that writeup needs to be
               shared with
    Returns:
        (True, message) if validated, (False, message) if
        validation fails or throws exception
    '''
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
            ent = syn.getPermissions(submission['entityId'], AUTHENTICATED_USERS)
            assert "READ" in ent and "DOWNLOAD" in ent, message
            ent = syn.getPermissions(submission['entityId'])
            assert "READ" in ent, message
        if admin is not None:
            message = (f"Please share your private directory ({submission['entityId']})"
                       f" with the Synapse user `{admin}` with `Can Download` permissions.")
            share_with.append(message)
            ent = syn.getPermissions(submission['entityId'], admin)
            assert "READ" in ent and "DOWNLOAD" in ent, message
    except SynapseHTTPError as syn_error:
        if syn_error.response.status_code == 403:
            raise AssertionError("\n".join(share_with))
        raise syn_error
    validation_status = {'valid': True,
                         'annotations': {},
                         'message': "Validated!"}
    return validation_status


def score1(submission_path, goldstandard_path):
    '''
    Scoring function number 1

    Args:
        submission_path:  Path to submission file
        goldstandard_path: Path to truth file

    Returns:
        Must return score dictionary and a scoring message
    '''
    print(submission_path)
    print(goldstandard_path)
    auc = 4
    bac = 3
    score = 1
    score_dict = dict(auc=round(auc, 4), bac=bac, score=score)
    message = "Your submission has been scored!"
    score_status = {'valid': True,
                    'annotations': score_dict,
                    'message': message}
    return score_status

def score2(submission_path, goldstandard_path):
    '''
    Scoring function number 2

    Args:
        submission_path:  Path to submission file
        goldstandard_path: Path to truth file

    Returns:
        Must return score dictionary and a scoring message
    '''
    print(submission_path)
    print(goldstandard_path)
    # Score against goldstandard
    auc = 4
    bac = 3
    score = 1
    score_dict = dict(auc=round(auc, 4), bac=bac, score=score)
    message = "Your submission has been scored!"
    score_status = {'valid': True,
                    'annotations': score_dict,
                    'message': message}
    return score_status


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
    },
    # Write ups don't need to be scored
    # If goldstandard path is None, the submissions will not be scored
    {
        'id': 3,
        'scoring_func': no_score,
        'validation_func': validate_writeup,
        'goldstandard_path': None
    }
]
