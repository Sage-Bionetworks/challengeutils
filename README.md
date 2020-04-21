
# Sage Bionetworks Challenge Utilities

The `challengeutils` package provides an interface for managing Sage Bionetworks Challenges administered using [Synapse](https://www.synapse.org), including [DREAM Challenges](http://dreamchallenges.org/). This package is being actively developed and maintained by DREAM and Informatics & Biocomputing (IBC), Computational Oncology Group at Sage Bionetworks.

Automation | Status
-----------|-------
[![Docker Automated](https://img.shields.io/docker/automated/sagebionetworks/challengeutils.svg)](https://hub.docker.com/r/sagebionetworks/challengeutils/) | ![Docker Build](https://img.shields.io/docker/build/sagebionetworks/challengeutils.svg)
pypi | [![Get challengeutils from PyPI](https://img.shields.io/pypi/v/challengeutils.svg)](https://pypi.python.org/pypi/challengeutils)
travis | [![Build Status master branch](https://travis-ci.org/Sage-Bionetworks/challengeutils.svg?branch=master)](https://travis-ci.org/Sage-Bionetworks/challengeutils)


## Install

```
pip install challengeutils
challengeutils -v
```

## Usage

Below is documentation for some of the key features in the `challengeutils` command line client.  The documentation can be found [here](https://sage-bionetworks.github.io/challengeutils/).

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

## Contributing

### Fork and clone this repository

See the [Github docs](https://help.github.com/articles/fork-a-repo/) for how to make a copy (a fork) of a repository to your own Github account.

Then, [clone the repository](https://help.github.com/articles/cloning-a-repository/) to your local machine so you can begin making changes.

Add this repository as an [upstream remote](https://help.github.com/en/articles/configuring-a-remote-for-a-fork) on your local git repository so that you are able to fetch the latest commits.

On your local machine make sure you have the latest version of the `develop` branch:

```
git checkout develop
git pull upstream develop
```

### The development life cycle

1. Pull the latest content from the `develop` branch of this central repository (not your fork).
1. Create a feature branch which off the `develop` branch. If there is a GitHub issue that you are addressing, name the branch after the issue with some more detail (like `issue-123-add-some-new-feature`).
1. After completing work and testing locally (see below), push to your fork.
1. In Github, create a pull request from the feature branch of your fork to the `develop` branch of the central repository.

> *A code maintainer must review and accept your pull request.* A code review (which happens with both the contributor and the reviewer present) is required for contributing. This can be performed remotely (e.g., Skype, Hangout, or other video or phone conference).

This package uses [semantic versioning](https://semver.org/) for releasing new versions. The version should be updated on the `develop` branch as changes are reviewed and merged in by a code maintainer. The version for the package is maintained in the [challengeutils/__version__.py](challengeutils/__version__.py) file.  A github release should also occur every time `develop` is pushed into `master` and it should match the version for the package.

### Testing

Please add tests for new code. These might include unit tests (to test specific functionality of code that was added to support fixing the bug or feature), integration tests (to test that the feature is usable - e.g., it should have complete the expected behavior as reported in the feature request or bug report), or both.

This package uses [`pytest`](https://pytest.org/en/latest/) to run tests. The test code is located in the [test](./test) subdirectory.

Here's how to run the test suite:

```
pytest -vs tests/
```

Tests are also run automatically by Travis on any pull request and are required to pass before merging.
