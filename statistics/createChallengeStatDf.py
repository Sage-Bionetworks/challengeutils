import synapseclient
import pandas as pd
# import calendar
# import time
syn = synapseclient.login()


def getUniqMembers(listOfTeams):
    """
    :param listOfTeams:  Takes a list of teams
    """
    allmembers = set()
    for i in teams:
        members = syn.getTeamMembers(i)
        for member in members:
            members.add(member['member']['ownerId'])
    return(members)


# Create challenge locations
def createChallengeLocationList(allMembers, locationFileName):
    locations = []
    for member in allMembers:
        user = syn.getUserProfile(member)
        loc = user.get('location', None)
        if loc is not None and loc != '':
            locations.append(loc)
    with open(locationFileName, 'w+') as location_doc:
        location_doc.write('locations\n')
        for i in locations:
            location_doc.write(i.encode('utf-8') + "\n")


# EDIT syn10163902 TO ADD CHALLENGES
challenge_landscape = syn.tableQuery(
    'select challenge, participants, preregistrants, "year" from syn10163902')
challenge_landscapedf = challenge_landscape.asDataFrame()
challenge_landscapedf.drop_duplicates("challenge", inplace=True)
all_teams = []
all_participants = []
all_locations = []
for challenge in challenge_landscapedf['challenge']:
    print(challenge)
    challenge_team = challenge_landscapedf['participants'][
        challenge_landscapedf['challenge'] == challenge].values[0]
    preregistration_team = challenge_landscapedf['preregistrants'][
        challenge_landscapedf['challenge'] == challenge].values[0]
    teams = [str(challenge_team)]
    if not pd.isnull(preregistration_team):
        teams.append(str(int(preregistration_team)))
    all_teams.append(",".join(teams))
    challenge_participants = set()
    participant_location = []
    for chal_team in teams:
        team = syn.getTeam(chal_team)
        for member in syn.getTeamMembers(team):
            challenge_participants.add(member['member']['userName'])
            member = syn.getUserProfile(member['member']['ownerId'])
            loc = member.get('location', None)
            if loc is not None and loc != '':
                participant_location.append(loc)
    all_participants.append(",".join(challenge_participants))
    all_locations.append("|".join(participant_location))

challenge_datadf = pd.DataFrame()
challenge_datadf['challenges'] = challenge_landscapedf['challenge']
challenge_datadf['teams'] = all_teams
challenge_datadf['createdOn'] = challenge_landscapedf['year']
challenge_datadf['users'] = all_participants
challenge_datadf['locations'] = all_locations
challenge_datadf.to_csv(
    "challenge_stats.tsv",
    index=False,
    sep='\t',
    encoding='utf-8')
