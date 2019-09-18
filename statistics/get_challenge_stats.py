import synapseclient
import pandas as pd
import challengeutils
import math
import requests
import json


def create_docker_submission_stats(syn, evalid, round_start, round_end,
                                   round_value, subchallenge, challenge):
    '''
    Get docker challenge submission statistics
    '''
    query_string = 'select * from evaluation_{}'.format(evalid)
    query_results = \
        challengeutils.utils.evaluation_queue_query(syn, query_string)
    submission_statsdf = pd.DataFrame()
    for result in query_results:
        time_submit = result['createdOn']
        if time_submit > round_start and time_submit <= round_end:
            # milliseconds
            submission_run_start = int(result['RUN_START'])
            submission_run_end = int(result['RUN_END'])
            run_duration_minutes = math.ciel(
                (submission_run_end - submission_run_start)/60000.0)

            subdf = pd.DataFrame({"team": result['submitterId'],
                                  "submissionId": result['id'],
                                  "runTimeMinutes": run_duration_minutes,
                                  "sc": subchallenge,
                                  "round": round_value,
                                  "status": result['status'],
                                  "challenge": challenge}, index=[0])
            submission_statsdf = submission_statsdf.append(subdf)
    return(submission_statsdf)


def get_team_usernames(syn, team):
    '''
    Get team usernames

    Args:
        syn: Synapse object
        team: Synapse team id or object

    Returns:
        list of usernames
    '''
    members = syn.getTeamMembers(team)
    usernames = [member['member']['ownerId'] for member in members]
    return(usernames)


def get_uniq_members(syn, team_list):
    """
    Return unique usernames from a list of teams

    Args:
        syn: Synapse object
        team_list: List of Synapse team ids

    Return:
        set of usernames
    """
    allmembers = set()
    for team in team_list:
        usernames = get_team_usernames(syn, team)
        allmembers.update(usernames)
    return(allmembers)


# Create challenge locations
def get_challenge_participant_locations(syn, usernames,
                                        location_filename=None):
    '''
    Get challenge participant locations

    Args:
        syn: Synapse object
        usernames: List of synapse user ids
        location_filename: If specified, writes locations to a file

    Returns:
        set of locations
    '''
    locations = set()
    for member in usernames:
        user = syn.getUserProfile(member)
        loc = user.get('location', None)
        if loc is not None and loc != '':
            locations.add(loc)
    if location_filename is not None:
        with open(location_filename, 'w+') as location_doc:
            location_doc.write('locations\n')
            for loc in locations:
                location_doc.write(loc.encode('utf-8') + "\n")
    return(locations)


def get_team_user_map_json(teamid):
    '''
    Get Synapse team user map json info

    Args:
        teamid: Synapse team id

    Returns:
        Json with information of users in team
    '''
    map_json_url = "https://s3.amazonaws.com/geoloc.sagebase.org/{}.json"
    team_json_url = map_json_url.format(teamid)
    response = requests.get(team_json_url)
    team_json = response.json()
    return(team_json)


def main():
    # EDIT syn10163902 TO ADD CHALLENGES
    syn = synapseclient.login()
    challenge_landscape = syn.tableQuery(
        'select challenge, challengeParticipants, challengePreregistrants, '
        'challengeYear from syn10163902')
    challenge_landscapedf = challenge_landscape.asDataFrame()
    challenge_landscapedf.drop_duplicates("challenge", inplace=True)
    all_teams = []
    all_participants = []
    all_locations = []
    for challenge in challenge_landscapedf['challenge']:
        print(challenge)
        challenge_infodf = challenge_landscapedf.query(
            'challenge == "{}"'.format(challenge))
        challenge_team = challenge_infodf['challengeParticipants'].iloc[0]
        preregistration_team = \
            challenge_infodf['challengePreregistrants'].iloc[0]
        teams = [str(int(challenge_team))]
        if not pd.isnull(preregistration_team):
            teams.append(str(int(preregistration_team)))
        all_teams.append(",".join(teams))
        challenge_participants = get_uniq_members(syn, teams)
        print(len(challenge_participants))
        participant_location = \
            get_challenge_participant_locations(syn, challenge_participants)
        all_participants.append(",".join(challenge_participants))
        all_locations.append("|".join(participant_location))

    challenge_datadf = pd.DataFrame()
    challenge_datadf['challenges'] = challenge_landscapedf['challenge']
    challenge_datadf['teams'] = all_teams
    challenge_datadf['year'] = challenge_landscapedf['challengeYear']
    challenge_datadf['users'] = all_participants
    challenge_datadf['locations'] = all_locations
    challenge_datadf['number_participants'] = \
        [len(user.split(",")) for user in challenge_datadf['users']]
    challenge_datadf.to_csv(
        "challenge_stats.tsv",
        index=False,
        sep='\t',
        encoding='utf-8')

    all_json = []
    for teams in all_teams:
        challenge_teams = teams.split(",")
        for team in challenge_teams:
            team_json = get_team_user_map_json(team)
            all_json.extend(team_json)

    with open("teams_json.json", 'w') as outfile:
        json.dump(all_json, outfile)


if __name__ == "__main__":
    main()
