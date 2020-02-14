"""Download the current leading submission for boot ladder boot method"""
import os

from . import utils


def get_submitterid_from_submission_id(syn, submissionid, queue,
                                       verbose=False):
    """Gets submitterid from submission id

    Args:
        syn: Synapse connection
        submissionid: Submission id
        queue: Evaluation queue id
        verbose: Boolean value to print

    Returns:
        Submitter id
    """
    query = ("select submitterId from evaluation_{} "
             "where objectId == '{}'".format(queue, submissionid))
    generator = utils.evaluation_queue_query(syn, query)
    lst = list(generator)
    if not lst:
        raise ValueError('submission id {} not in queue'.format(submissionid))
    submission_dict = lst[0]
    submitterid = submission_dict['submitterId']
    if verbose:
        print("submitterid: " + submitterid)
    return submitterid


def get_submitters_lead_submission(syn, submitterid, queue,
                                   cutoff_annotation, verbose=False):
    """Gets submitter's lead submission

    Args:
        submitterid: Submitter id
        queue: Evaluation queue id
        cutoff_annotation: Boolean cutoff annotation key
        verbose: Boolean value to print

    Returns:
        previous_submission.csv or None
    """
    query = ("select objectId from evaluation_{} where submitterId == '{}' "
             "and prediction_file_status == 'SCORED' and {} == 'true' "
             "order by createdOn DESC".format(queue, submitterid,
                                              cutoff_annotation))

    generator = utils.evaluation_queue_query(syn, query)
    lst = list(generator)
    if lst:
        sub_dict = lst[0]
        objectid = sub_dict['objectId']
        if verbose:
            print("Dowloading submissionid: " + objectid)
        sub = syn.getSubmission(objectid, downloadLocation=".")
        os.rename(sub.filePath, "previous_submission.csv")
        return "previous_submission.csv"
    print("Downloading no file")
    return None


def download_current_lead_sub(syn, submissionid, status,
                              cutoff_annotation, verbose=False):
    """Downloads current leading submission

    Args:
        syn: Synapse connection
        submissionid: Submission id
        status: Submission status
        cutoff_annotation: Boolean cutoff annotation key
        verbose: Boolean value to print

    Returns:
        Path to current leading submission or None
    """
    if status == "VALIDATED":
        current_sub = syn.getSubmission(submissionid, downloadFile=False)
        queue_num = current_sub['evaluationId']
        submitterid = get_submitterid_from_submission_id(syn, submissionid,
                                                         queue_num, verbose)
        path = get_submitters_lead_submission(syn, submitterid, queue_num,
                                              cutoff_annotation, verbose)
        return path
    return None
