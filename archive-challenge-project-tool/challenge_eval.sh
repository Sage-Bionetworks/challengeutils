# Automation of validation and scoring
# Make sure you point to the directory where challenge.py belongs and a log directory must exist for the output
cd /
#---------------------
#Validate submissions
#---------------------
#Remove --send-messages to do rescoring without sending emails to participants
python challenge.py --challengeName $CHALLENGE_NAME -u $SYNAPSE_USERNAME -p $SYNAPSE_PASSWORD --send-messages --notifications --acknowledge-receipt validate 9603284 --admin 3336298 #>> log/score.log 2>&1

#--------------------
#Archive submissions
#--------------------
python challenge.py --challengeName $CHALLENGE_NAME -u $SYNAPSE_USERNAME -p $SYNAPSE_PASSWORD --notifications archive 9603284 #>> log/score.log 2>&1
