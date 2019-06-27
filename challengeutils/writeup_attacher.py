import pandas as pd
from synapseclient.annotations import to_submission_status_annotations
from . import utils


def append_writeup_to_main_submission(row, syn):
    '''
    Helper function that appends the write up synapse id and archived
    write up synapse id on the main submission

    Args:
        row: Dictionary row['team'], row['objectId'], row['archived'],
             row['entityId']
        syn: synapse object
    '''
    if pd.isnull(row['archived']):
        print("NO WRITEUP: " + row['team'])
    else:
        status = syn.getSubmissionStatus(row['objectId'])
        add_writeup_dict = {
            'writeUp': row['entityId'], 'archivedWriteUp': row['archived']}

        add_writeup = to_submission_status_annotations(
            add_writeup_dict, is_private=False)
        new_status = utils.update_single_submission_status(
            status, add_writeup)
        syn.store(new_status)


def attach_writeup(syn, writeup_queueid, submission_queueid):
    '''
    Attach the write up to the submission queue

    Args:
        writeup_queueid:   Write up evaluation queue id
        submission_queueid: Submission queue id
    '''
    writeups = list(utils.evaluation_queue_query(
        syn,
        "select team, entityId, archived from evaluation_{} "
        "where status == 'VALIDATED'".format(writeup_queueid)))
    submissions = list(utils.evaluation_queue_query(
        syn,
        "select objectId, team from evaluation_{} "
        "where status == 'SCORED'".format(submission_queueid)))
    writeupsdf = pd.DataFrame(writeups)
    submissionsdf = pd.DataFrame(submissions)
    submissions_with_writeupsdf = \
        submissionsdf.merge(writeupsdf, on="team", how="left")

    submissions_with_writeupsdf.apply(
        lambda row: append_writeup_to_main_submission(row, syn), axis=1)
