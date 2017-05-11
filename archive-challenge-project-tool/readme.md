Archiving Challenge Participant Write-Ups
=========================================

1 ) Set local environment variable names in commandline
```
SYNAPSE_USERNAME=synapseuser
SYNAPSE_PASSWORD=synapsepass
CHALLENGE_NAME=challenge
```

2 ) Set the `ADMIN_USER_IDS` in `challenge_config.py` by giving it a list of admin users that you want to have emails sent to in case of errors.

3 ) Set the defaults in `messages.py`. The `scoring_script` parameter will be the name that is signed for all emails sent to participants
```
defaults = dict(
    challenge_instructions_url = "https://www.synapse.org/...",
    support_forum_url = "https://www.synapse.org/#!Synapse:{synIdhere}/discussion/default",
    scoring_script = "the scoring script")
```
