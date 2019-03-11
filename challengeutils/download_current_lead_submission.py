import utils
import os


def get_submitterid_from_submission_id(
        syn, submissionid, queue, verbose=False):
    query = ("select * from " + queue +
             " where objectId == " + str(submissionid))
    generator = utils.evaluation_queue_query(syn, query)
    lst = list(generator)
    if len(lst) == 0:
        raise Exception('submission id {} not in queue'.format(submissionid))
    submission_dict = lst[0]
    submitterid = submission_dict['submitterId']
    if verbose:
        print("submitterid: " + submitterid)
    return(submitterid)


def get_submitters_lead_submission(
        syn, submitterid, queue,
        cutoff_annotation, verbose=False):
    query = ("select * from " + queue +
             " where submitterId == " + str(submitterid) +
             " and prediction_file_status == 'SCORED' and '" +
             cutoff_annotation + "' == 'true'" +
             " order by createdOn DESC")
    generator = utils.evaluation_queue_query(syn, query)
    lst = list(generator)
    if len(lst) > 0:
        sub_dict = lst[0]
        objectid = sub_dict['objectId']
        if verbose:
            print("Dowloading submissionid: " + objectid)
        sub = syn.getSubmission(objectid, downloadLocation=".")
        os.rename(sub.filePath, "previous_submission.csv")
        return("previous_submission.csv")
    else:
        print("Downloading no file")


def download_current_lead_sub(
        syn, submissionid, status, cutoff_annotation, verbose=False):
    if status == "VALIDATED":
        current_sub = syn.getSubmission(submissionid, downloadFile=False)
        queue_num = current_sub['evaluationId']
        queue = "evaluation_" + queue_num
        submitterid = get_submitterid_from_submission_id(
            syn, submissionid, queue, verbose)
        path = get_submitters_lead_submission(
            syn, submitterid, queue, cutoff_annotation, verbose)
        return(path)
