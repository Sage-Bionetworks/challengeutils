'''
Challenge helper functions
'''
import os
import sys
import time

import synapseclient
import synapseutils

from . import challenge, utils

WORKFLOW_LAST_UPDATED_KEY = "orgSagebionetworksSynapseWorkflowOrchestratorWorkflowLastUpdated"
WORKFLOW_START_KEY = "orgSagebionetworksSynapseWorkflowOrchestratorExecutionStarted"
TIME_REMAINING_KEY = "orgSagebionetworksSynapseWorkflowOrchestratorTimeRemaining"


def rename_submission_files(syn, evaluationid, download_location="./",
                            status="SCORED"):
    '''
    This function renames the submission files of an evaluation queue.
    For many challenges we require participants to submit files that are
    named one thing such as prediction.csv. This function renames them to

        submitter_date_filename

    Args:
        syn: synapse object
        evaluationid:  Id of Evaluation queue
        download_location:  location to download files to (Default is ./)
        status: The submissions to download (Default is SCORED)
    '''
    submission_bundle = syn.getSubmissionBundles(evaluationid, status=status)
    for sub, status in submission_bundle:
        if sub.get("teamId") is not None:
            submitter = syn.getTeam(sub.get("teamId"))['name']
        else:
            submitter = syn.getUserProfile(sub.userId)['userName']
        date = sub.createdOn
        submission_ent = \
            syn.getSubmission(sub.id, downloadLocation=download_location)
        filename = os.path.basename(submission_ent.filePath)
        newname = submitter+"___"+date+"___"+filename
        newname = newname.replace(' ', '_')
        os.rename(filename, newname)
        print(newname)


def create_team_wikis(syn, synid, templateid, tracker_table_synid):
    """
    Function that creates wiki pages from a template by looking at teams that
    are registered for a challenge.  The teams that have a wiki made for them
    Are stored into a trackerTable that has columns wikiSynId, and teamId

    Args:
        synId: Synapse id of challenge project
        templateId:  Synapse id of the template
        trackerTableSynId: Synapse id of Table that tracks if wiki pages
                           have been made per team
    """
    challenge_ent = syn.get(synid)

    challenge_obj = challenge.get_challenge(syn, challenge_ent)
    registered_teams = syn._GET_paginated(
        "/challenge/{}/challengeTeam".format(challenge_obj.id))
    for i in registered_teams:
        submitted_teams = syn.tableQuery(
            "SELECT * FROM {} where teamId = '{}'".format(
                tracker_table_synid, i['teamId']))
        if len(submitted_teams.asDataFrame()) == 0:
            team = syn.getTeam(i['teamId'])
            # The project name is the challenge project name and team name
            project = syn.store(synapseclient.Project("{} {}".format(
                challenge_ent.name, team.name)))
            # Give admin access to the team
            syn.setPermissions(
                project, i['teamId'],
                accessType=['DELETE', 'CHANGE_SETTINGS', 'MODERATE',
                            'CREATE', 'READ', 'DOWNLOAD', 'UPDATE',
                            'CHANGE_PERMISSIONS'])
            wiki_copy = synapseutils.copy(syn, templateid, project.id)
            # syn.sendMessage(i[])
            # Store copied synId to tracking table
            tracking_table = synapseclient.Table(
                tracker_table_synid, [[wiki_copy[templateid], i['teamId']]])
            syn.store(tracking_table)


def kill_docker_submission_over_quota(syn, evaluation_id, quota=sys.maxsize):
    '''
    Kills any docker container that exceeds the run time quota
    Rerunning submissions will require setting TimeRemaining annotation
    to a positive integer

    Args:
        syn (obj): Synapse object
        evaluation_id (int): Synapse evaluation queue id
        quota (int): Quota in milliseconds. Default is sys.maxsize.
                     One hour is 3600000.
    '''
    if not isinstance(quota, int):
        raise ValueError("quota must be an integer")
    if quota <= 0:
        raise ValueError("quota must be larger than 0")

    evaluation_query = (f"select * from evaluation_{evaluation_id} where "
                        "status == 'EVALUATION_IN_PROGRESS'")
    query_results = utils.evaluation_queue_query(syn, evaluation_query)

    for result in query_results:
        # If last updated and start doesn't exist, set to 0
        last_updated = int(result.get(WORKFLOW_LAST_UPDATED_KEY, 0))
        start = int(result.get(WORKFLOW_START_KEY, 0))
        model_run_time = last_updated - start
        if model_run_time > quota:
            status = syn.getSubmissionStatus(result['objectId'])
            add_annotations = {TIME_REMAINING_KEY: 0}
            status = utils.update_single_submission_status(status,
                                                           add_annotations)
            syn.store(status)

    # Rerunning submissions will require setting this
    # annotation to a positive integer


def archive_writeup(syn, evaluation, stat="VALIDATED", reArchive=False):
    """
    Archive the submissions for the given evaluation queue and
    store them in the destination synapse folder.

    :param evaluation: a synapse evaluation queue or its ID
    :param query: a query that will return the desired submissions.
                  At least the ID must be returned. Defaults to:
                  'select * from evaluation_[EVAL_ID] where status=="SCORED"'
    """
    if type(evaluation) != synapseclient.Evaluation:
        evaluation = syn.getEvaluation(evaluation)

    print("\n\nArchiving", evaluation.id, evaluation.name)
    print("-" * 60)

    for sub, status in syn.getSubmissionBundles(evaluation, status=stat):
        # retrieve file into cache and copy it to destination
        checkIfArchived = filter(
            lambda x: x.get("key") == "archived",
            status.annotations['stringAnnos'])
        if len(list(checkIfArchived)) == 0 or reArchive:
            projectEntity = synapseclient.Project(
                'Archived {} {} {} {}'.format(
                    sub.name.replace("&", "+").replace("'", ""),
                    int(round(time.time() * 1000)),
                    sub.id,
                    sub.entityId))
            entity = syn.store(projectEntity)
            adminPriv = [
                'DELETE', 'DOWNLOAD', 'CREATE', 'READ', 'CHANGE_PERMISSIONS',
                'UPDATE', 'MODERATE', 'CHANGE_SETTINGS']
            syn.setPermissions(entity, "3324230", adminPriv)
            synapseutils.copy(syn, sub.entityId, entity.id)
            archived = {"archived": entity.id}
            status = utils.update_single_submission_status(status, archived)
            syn.store(status)
