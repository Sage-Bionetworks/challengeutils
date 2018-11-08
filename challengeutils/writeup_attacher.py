import synapseclient
import urllib
import argparse
import challengeutils
import pandas as pd

def append_writeup_to_main_submission(row, syn):
    '''
    Helper function that appends the write up synapse id and archived write up synapse id 
    on the main submission

    params:
        row:  Dictionary row['team'], row['objectId'], row['archived'], row['entityId']
        syn: synapse object
    '''
    if pd.isnull(row['archived']):
        print("NO WRITEUP: " + row['team'])
    else:
        status = syn.getSubmissionStatus(row['objectId'])
        add_writeup_dict = {'writeUp':row['entityId'],'archivedWriteUp':row['archived']}

        add_writeup = synapseclient.annotations.to_submission_status_annotations(add_writeup_dict, is_private = False)
        new_status = challengeutils.utils.update_single_submission_status(status, add_writeup)
        syn.store(new_status)

def attach_writeup(syn, writeup_queueid, submission_queueid):
    '''
    Attach the write up to the submission queue

    params:
        writeup_queueid:   Write up evaluation queue id
        submission_queueid: Submission queue id
    '''
    writeups = list(challengeutils.utils.evaluation_queue_query(syn, "select team, entityId, archived from evaluation_%s where status == 'VALIDATED'" % writeup_queueid))
    submissions = list(challengeutils.utils.evaluation_queue_query(syn, "select objectId, team from evaluation_%s where status == 'SCORED'" % submission_queueid)) 
    writeupsdf = pd.DataFrame(writeups)
    submissionsdf = pd.DataFrame(submissions)
    submissions_with_writeupsdf = submissionsdf.merge(writeupsdf,on="team",how="left")

    submissions_with_writeupsdf.apply(lambda row: append_writeup_to_main_submission(row, syn),axis=1)

def perform_main(syn, args):
    attach_writeup(syn, args.writeupqueue, args.submissionqueue)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Attach writeup and archived writeups to challenge queue annotations')
    parser.add_argument("writeupqueue", type=str, help='Write up submission queue evaluation id')
    parser.add_argument("submissionqueue", type=str, help='Challenge submission queue evaluation id')
    args = parser.parse_args()
    syn = synapseclient.login()
    perform_main(syn, args)


