# DREAM-Utilities

**Merging wikis**
For all challenges, you should be editting the staging site and then using the merge script to mirror staging to live site.  The script will compare wiki titles between the staging and live site and update the live site with respect to what has changed on the staging site.

```
#python mergeWiki.py "synIdOfEntity" "synIdOfDestination"
python mergeWiki.py "syn12345" "syn23456"
```