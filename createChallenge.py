def create_team(name, description):
    return syn.store(Team(name=name, description=description, canPublicJoin=True))


def create_challenge_object(project, participants_team):
    challenge_json = {'participantTeamId':utils.id_of(participants_team), 'projectId':utils.id_of(project)}
    return DictObject(**syn.restPOST("/challenge", body=json.dumps(challenge_json)))

def create_evaluation_queue(syn, name, parentId, description, submissionInstructionsMessage, status="OPEN"):
    evaluation = syn.store(Evaluation(
      name=name,
      description=description,
      status=status,
      contentSource=parentId,
      submissionInstructionsMessage=submissionInstructionsMessage,
      submissionReceiptMessage="Thanks for submitting to %s!" % name,
      quota=dict(numberOfRounds=1,
                 roundDurationMillis=1000*60*60*48, ## 48 hours
                 submissionLimit=20,
                 firstRoundStart=datetime.now().strftime(synapseclient.utils.ISO_FORMAT))))
    print "Created Evaluation %s %s" % (evaluation.id, evaluation.name)
    return(queue)

def set_up(challengeName):
    # Create the Challenge Project
    challenge_project = syn.store(Project(name=challengeName))
    print "Created project %s %s" % (challenge_project.id, challenge_project.name)
    challenge_staging_project = syn.store(Project(name=challengeName + " Staging"))
    print "Created project %s %s" % (challenge_staging_project.id, challenge_staging_project.name)

    # evaluation = syn.store(Evaluation(
    #     name=challenge_project.name,
    #     contentSource=challenge_project.id,
    #     status="OPEN",
    #     submissionInstructionsMessage="To submit to the XYZ Challenge, send a tab-delimited file as described here: https://...",
    #     submissionReceiptMessage="Your submission has been received. For further information, consult the leader board at https://..."),
    #     quota=dict(numberOfRounds=1,
    #                roundDurationMillis=1000*60*60*48, ## 48 hours
    #                submissionLimit=20,
    #                firstRoundStart=datetime.now().strftime(synapseclient.utils.ISO_FORMAT)))
    # print "Created Evaluation %s %s" % (evaluation.id, evaluation.name)

    # Create teams for participants and administrators
    participants_team = syn.store(Team(name=challengeName+' Participants', description='A participant team for people who have joined the %s' % challengeName))
    print "Created team %s(%s)" % (participants_team.name, participants_team.id)

    preregistrants_team = syn.store(Team(name=challengeName+' Preregistrants', description='A preregistrant team for people who have preregistered for the %s' % challengeName))
    print "Created team %s(%s)" % (preregistrants_team.name, preregistrants_team.id)

    admin_team = syn.store(Team(name=challengeName+' Administrators', description='A team for %s administrators' % challengeName))
    print "Created team %s(%s)" % (admin_team.name, admin_team.id)

    # give the teams permissions on challenge artifacts
    # see: http://rest.synapse.org/org/sagebionetworks/repo/model/ACCESS_TYPE.html
    # see: http://rest.synapse.org/org/sagebionetworks/evaluation/model/UserEvaluationPermissions.html
    syn.setPermissions(challenge_project, admin_team.id, ['CREATE', 'READ', 'UPDATE', 'DELETE', 'CHANGE_PERMISSIONS', 'DOWNLOAD', 'UPLOAD'])
    syn.setPermissions(challenge_staging_project, admin_team.id, ['CREATE', 'READ', 'UPDATE', 'DELETE', 'CHANGE_PERMISSIONS', 'DOWNLOAD', 'UPLOAD'])

    # syn.setPermissions(challenge_project, participants_team.id, ['READ', 'DOWNLOAD'])

    #syn.setPermissions(evaluation, admin_team.id, ['CREATE', 'READ', 'UPDATE', 'DELETE', 'CHANGE_PERMISSIONS', 'DOWNLOAD', 'PARTICIPATE', 'SUBMIT', 'DELETE_SUBMISSION', 'UPDATE_SUBMISSION', 'READ_PRIVATE_SUBMISSION'])
    #syn.setPermissions(evaluation, participants_team.id, ['CREATE', 'READ', 'UPDATE', 'PARTICIPATE', 'SUBMIT', 'READ_PRIVATE_SUBMISSION'])
    
    ## the challenge object associates the challenge project with the
    ## participants team
    challenge_object = create_challenge_object(challenge_project, participants_team)

    return dict(challenge_project=challenge_project,
                challenge_object=challenge_object,
                participants_team=participants_team,
                preregistrants_team = preregistrants_team,
                admin_team=admin_team)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--user", help="UserName", default=None)
    parser.add_argument("-p", "--password", help="Password", default=None)
    parser.add_argument("challengeName", help="Challenge name")

    parser_setup = subparsers.add_parser('setup', help="create challenge artifacts")
    parser_setup.set_defaults(func=command_setup)