*********
Changelog
*********

This changelog is used to track all major changes to **challengeutils**.

For older releases, visit the `GitHub releases`_.

.. _Github releases: https://github.com/Sage-Bionetworks/challengeutils/releases

v4.0.1
------
.. Important::
    **Support for synapseclient<2.3.0 is no longer available**; upgrade to the
    latest version with:

    .. code:: console

        $ pip install synapseclient --upgrade

.. Important::
    **Support for Python 3.6 is will be dropped in the later
    half of this year.

- Support `Python` 3.9
- Deprecate `helpers.py` and create `stop_submissions_over_quota` function
- Fix conditionals when validating permissions for project submissions


v3.2.0
------

- Added push and pull Synapse wiki feature


v3.1.0
------
.. Important::
    **Support for synapseclient<2.2.0 is no longer available**; upgrade to the
    latest version with:

    .. code:: console

        $ pip install synapseclient --upgrade

- Remove team member from team
- Upgrade synapseclient used
- Retrieve number of members given team name / id.
- Move functions to team module


v3.0.0
------

.. Important::
    **Support for synapseclient<2.1.0 is no longer available**; upgrade to the
    latest version with:

    .. code:: console

        $ pip install synapseclient --upgrade

- Add Synapse `Thread` and `Reply` module
- Rename command line client functions to have dashes inbetween words (e.g. `challengeutils create-challenge`).  This is a breaking change, but is done to standardize the command line client commands.
- `validate_project` now returns errors that are `str` type instead of `list`


v2.2.0
------
- Added `delete_submission`, `validate_project` and `archive_project` functions
- `Submission Views` are now supported in `Synapse`.  Updating annotations now adds both `annotations` and `submissionAnnotations`.


v2.1.0
------
- Remove `invite_member_to_team` function as functionality is in `synapseclient`
- `challengeutils.discussion.copy_thread` now also copies replies instead of just the thread
- Fixed `challengeutils.createchallenge` function bug - Do not use `Challenge` class to instantiate the body of `restPOST` or `restPUT` calls
- Refactored and added tests for `challengeutils.mirrorwiki`
- `challengeutils.mirrorwiki.mirrorwiki` renamed to `challengeutils.mirrorwiki.mirror`
- Added `dryrun` parameter to let users know which pages would be updated in `challengeutils.mirrorwiki`
- Add automation of code coverage
- Revise documentation

v2.0.1
------
- Added `CONTRIBUTING.md`
- Revised `README.md`
- Added `CODE_OF_CONDUCT.md`
- Update `version`


v2.0.0
------

.. Important::
    **Support for synapseclient<2.0.0 is no longer available**; upgrade to the
    latest version with:

    .. code:: console

        $ pip install synapseclient --upgrade

- Refine ``challenge`` services
- Update library dependency, e.g. using ``unittest.mock`` instead of ``mock``
- Fix queue query CLI errors
- Fix ``mirrorwiki`` error
- **Release is 2.0.0.dev0 on pypi**

v1.6.0
------

**synapseclient 2.0.0 is now fully supported!**

- Update the live page wiki content that ``createchallenge`` would create
- Show URLs of projects and teams created by ``createchallenge``
- Auto-build sphinx docs to ``gh-pages`` with ``gh-actions``. thus removing ``readthedocs`` dependency

v1.5.2
------

- Lock down ``synapseclient==1.9.4`` version in ``requirements.txt``

v1.5.1
------

Versioning fix.

v1.5.0
------

- Add auto-generated documentation
- Fix CLI command for annotating submission
- Add ``setevaluationquota`` command
- **Release is 1.5.0.dev0 on pypi**
