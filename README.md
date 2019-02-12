[![Docker Automated](https://img.shields.io/docker/automated/sagebionetworks/challengeutils.svg)](https://hub.docker.com/r/sagebionetworks/challengeutils/) ![Docker Build](https://img.shields.io/docker/build/sagebionetworks/challengeutils.svg)  

# Sage Bionetworks Challenge Utilities

The `challengeutils` package provides an interface for managing Sage Bionetworks Challenges administered using [Synapse](https://www.synapse.org), including [DREAM Challenges](http://dreamchallenges.org/).

## Install

```
pip install git+https://github.com/Sage-Bionetworks/challengeutils.git
```

## Usage

View [here](http://htmlpreview.github.io/?https://github.com/Sage-Bionetworks/challengeutils/blob/master/docs/_build/singlehtml/index.html) for documentation to use this package in python scripts.  Below is documentation for the command line client.

```
challengeutils -h
```

**Creating Challenge Templates**

To begin all challenge infrastructure, you will want to create several Projects, and Teams.  This script pulls from a standard DREAM template and creates the Projects and Teams that you will need for a challenge.

```
challengeutils createchallenge "Challenge Name Here"
```

**Mirroring wikis**

For all challenges, you should be editting the staging site and then using the merge script to mirror staging to live site.  The script will compare wiki titles between the staging and live site and update the live site with respect to what has changed on the staging site.  Note, this is different from copying the wikis. To copy the wikis, please look at synapseutils.

```
challengeutils mirrorwiki syn12345 syn23456
```

**Querying an evaluation queue**

Evaluation queues offer a separate query service from the rest of Synapse.  This query function will print the leaderboard in a csv format in standard out.  Proceed [here](https://docs.synapse.org/rest/GET/evaluation/submission/query.html) to learn more about this query service.

```
challengeutils query "select objectId, status from evaluation_12345"
```

**Changing submission status**

This is a convenience function to change the status of a submission

```
challengeutils changestatus 1234545 INVALID
```

**Attaching write ups to main submission queue**

Most challenges require participants to submit a writeup.  Using the new archive-challenge-project-tool system of receiving writeups, this is a convenience function to merge the writeup and archived write up Synapse ids to the main challenge queue

```
challengeutils attachwriteup writeupid submissionqueueid
```

**Adding ACLs to Synapse Entities and Evaluation queues**

These two functions will give users or teams permissions to entities and evaluation queues.  By default the user is public if there is no user or team specified and the default permission is view.  For entities, the permission choices are "view", "download", "edit", "edit_and_delete", "admin".  

```
challengeutils setentityacl syn123545 user_or_team view
```

For evaluation queues, the permission choices are "view", "submit", "score", "admin". 

```
challengeutils setevaluationacl 12345 user_or_team score
```
