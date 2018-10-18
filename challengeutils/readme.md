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
challengeutils mirrorwiki "syn12345" "syn23456"
```

