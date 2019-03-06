import synapseclient
import challengeutils
import argparse
import os


def get_submitterid_from_submission_id(submissionid, queue, synapse_object):
    query = ("select * from " + queue + 
             " where objectId == " + str(submissionid))
    generator = challengeutils.utils.evaluation_queue_query(
            synapse_object, query)
    lst = list(generator)
    if len(lst) == 0:
        raise Exception('submission id {} not in queue'.format(submissionid))
    submission_dict = lst[0]
    submitterid = submission_dict['submitterId']
    if args.verbose:
        print("submitterid: " + submitterid)
    return(submitterid)

def get_submitters_lead_submission(submitterid, queue, synapse_object):
    query = ("select * from " + queue + 
             " where submitterId == " + str(submitterid) + 
             " and prediction_file_status == 'SCORED' and '" + 
             args.cutoff_annotation + "' == 'true'" +
             " order by createdOn DESC")
    generator = challengeutils.utils.evaluation_queue_query(syn, query)
    lst = list(generator)
    if len(lst) > 0:
        sub_dict = lst[0]
        objectid = sub_dict['objectId']
        if args.verbose:
            print("Dowloading submissionid: " + objectid)
        sub = syn.getSubmission(objectid, downloadLocation=".")
        os.rename(sub.filePath, "previous_submission.csv")
        return("previous_submission.csv")
    else:
        print("Dowloading no file")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-i", 
            "--submissionid", 
            required=True, 
            help="Int, or str(int) for submissionid, of current submission.")
    
    parser.add_argument(
            "-c",
            "--synapse_config", 
            required=True,
            help="credentials file")
    
    parser.add_argument(
            "-s",
            "--status", 
            required=True, 
            help="Submission status")
    
    parser.add_argument(
            "-v",
            "--verbose",
            action='store_false')
    
    parser.add_argument(
            "-a", 
            "--cutoff_annotation",
            default = "met_cutoff")
    
    args = parser.parse_args()
    
    if args.status == "VALIDATED":
        syn = synapseclient.Synapse(configPath=args.synapse_config)
        syn.login()
        current_sub = syn.getSubmissionStatus(args.submissionid)
        queue_num = current_sub.annotations['scopeId']
        queue = "evaluation_" + queue_num
        submitterid = get_submitterid_from_submission_id(
                args.submissionid, queue, syn)
        path = get_submitters_lead_submission(submitterid, queue, syn)
    
    
