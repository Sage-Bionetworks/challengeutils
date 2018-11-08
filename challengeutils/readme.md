## Challenge Utils

This package houses many tools used for challenges such as mirroring challenge staging sites to live sites or creating the conventional challenge templates. Please install the challengeutils package to use these scripts


**Creating Challenge Templates**

To begin all challenge infrastructure, you will want to create several Projects, and Teams.  This script pulls from a standard DREAM template and creates the Projects and Teams that you will need for a challenge.

```
challengeutils createchallenge "Challenge Name Here"
```

**Mirroring wikis**

For all challenges, you should be editting the staging site and then using the merge script to mirror staging to live site.  The script will compare wiki titles between the staging and live site and update the live site with respect to what has changed on the staging site.

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
