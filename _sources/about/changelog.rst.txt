*********
Changelog
*********

This changelog is used to track all major changes to **challengeutils**.

For older releases, visit the `GitHub releases`_.

.. _Github releases: https://github.com/Sage-Bionetworks/challengeutils/releases

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
