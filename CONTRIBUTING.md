# Contributing

Welcome, and thanks for your interest in contributing to `challengeutils`!

By contributing, you are agreeing that we may redistribute your work under this [license](LICENSE).

## How to contribute

### Reporting bugs or feature requests

File an [issue](https://github.com/Sage-Bionetworks/challengeutils/issues) in this repository. Please provide enough details for the developers to verify and troubleshoot your issue.

* **Use a clear and descriptive title** for the issue to identify the problem.
* **Describe the exact steps which reproduce the problem** in as many details as possible.
* **Provide specific examples to demonstrate the steps**. Include copy/pasteable snippets. If you are providing snippets in the issue, use [Markdown code blocks](https://help.github.com/articles/markdown-basics/#multiple-lines).
* **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
* **Explain which behavior you expected to see instead and why.**


### Fixing bugs and improvements

The open work items are tracked in the issues.  Issues marked as `Open` are ready for your contributions!

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
1. Create a feature branch which off the `develop` branch. The branch should be named the same as the issue you are working on (e.g., `fix-particular-bug`).
1. After completing work and testing locally (see below), push to your fork.
1. In Github, create a pull request from the feature branch of your fork to the `develop` branch of the central repository.  Make sure you link the issue in the pull request comment.

> A code review is required for contributing.


### Testing

All code added to the client must have tests.

`challengeutils` uses [`pytest`](https://docs.pytest.org/en/latest/) to run tests. The test code is located in the [test](./tests) subdirectory.

Here's how to run the test suite:

```
# Tests
pytest -vs tests/
```

To test a specific feature, specify the full path to the function to run:

```
# Test table query functionality from the command line client
pytest -vs tests/test_helpers.py::test_noquota_kill_docker_submission_over_quota
````