import synapseclient


def get_team_stats(teamId):
	members = syn.getTeamMembers(teamId)
	info = []
	for i in members:
		user = syn.getUserProfile(i['member']['ownerId'])
		name = user['firstName'] + " " + user['lastName']
		if user.get("location") is not None:
			location = user['location']
		else:
			location = ""
		info.append([user['userName'],name,location,user['ownerId']])
	temp = pd.DataFrame(info,columns = ['username','name','location','userId'])
	temp['name'] = [i.encode('utf-8').decode('utf-8') for i in temp['name']]
	#temp.to_csv("challenge_stats.csv", index=False, encoding='utf-8')
	return(temp)

def num_teams(evalId):
	submissions = syn.getSubmissionBundles(evalId)
	allTeams = set()
	for sub, status in submissions:
		team = filter(lambda x: x.get('key') == "team", status.annotations['stringAnnos'])[0]
		allTeams.add(team['value'])
	print(len(allTeams))

