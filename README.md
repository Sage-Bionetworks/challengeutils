# Sage Bionetworks Challenge Utilities

> [!WARNING]
> **Starting early 2024, this package will no longer be maintained.**  We are  in the process of creating a new-and-improved version of `challengeutils` - more information coming soon!

[![Get challengeutils from PyPI](https://img.shields.io/pypi/v/challengeutils.svg?style=for-the-badge&logo=pypi)](https://pypi.python.org/pypi/challengeutils) [![Docker Automated](https://img.shields.io/docker/automated/sagebionetworks/challengeutils.svg?style=for-the-badge&logo=docker)](https://hub.docker.com/r/sagebionetworks/challengeutils/) [![Docker Pull](https://img.shields.io/docker/pulls/sagebionetworks/challengeutils.svg?style=for-the-badge&logo=docker)](https://hub.docker.com/r/sagebionetworks/challengeutils/) [![Coverage Status](https://img.shields.io/coveralls/github/Sage-Bionetworks/challengeutils.svg?&style=for-the-badge&label=coverage&logo=Coveralls)](https://coveralls.io/github/Sage-Bionetworks/challengeutils)


`challengeutils` is a set of tools and commands that provides an interface for managing crowd-sourced challenges administered on [Synapse](https://www.synapse.org), including but not limited to, [DREAM Challenges](http://dreamchallenges.org/).  Its main purpose is to ease the process of creating, monitoring, and ending a challenge, as well as provide useful functions for post-competition analysis. _This package is being actively developed and maintained by DREAM and Informatics & Biocomputing (IBC), Computational Oncology Group at Sage Bionetworks._

## Documentation

`challengeutils` functionality is documented, [click here to check it out](https://sage-bionetworks.github.io/challengeutils/)!


## Installation

```
pip install challengeutils
challengeutils -v
```

This repository also uses [`pre-commit`](https://pre-commit.com/) to autolint files according to [Black's coding styles](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html). To run the hook in your local dev environment, enter the following:

```
pip install pre-commit
pre-commit install
```

Now `pre-commit` will run automatically on `git commit`! For example:

```
$ git commit -m 'update readme' -a
Check Yaml...........................................(no files to check)Skipped
Fix End of Files.........................................................Passed
Trim Trailing Whitespace.................................................Passed
black................................................(no files to check)Skipped
[add-pre-commit 75b4393] update readme
 1 file changed, 23 insertions(+)
```

## Contributing
Thinking about contributing to challengeutils? Get started by reading our [Contributor Guide](CONTRIBUTING.md).
