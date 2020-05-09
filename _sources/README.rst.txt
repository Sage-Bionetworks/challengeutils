**************
challengeutils
**************

.. image:: https://img.shields.io/docker/automated/sagebionetworks/challengeutils?logo=docker&logoColor=white&label=build
    :target: https://hub.docker.com/r/sagebionetworks/challengeutils/
    :alt: Docker build automation

.. image:: https://img.shields.io/pypi/v/challengeutils?logo=python&logoColor=white
    :target: https://pypi.python.org/pypi/challengeutils
    :alt: PyPI version

.. image:: https://img.shields.io/travis/Sage-Bionetworks/challengeutils?logo=travis-ci&logoColor=white
    :target: https://travis-ci.org/Sage-Bionetworks/challengeutils
    :alt: Build status

.. image:: https://img.shields.io/github/stars/Sage-Bionetworks/challengeutils?style=social
    :target: https://github.com/Sage-Bionetworks/challengeutils
    :alt: GitHub stars

**challengeutils** is a set of tools and commands that provides an interface
for  managing crowd-sourced challenges administered on Synapse_, including but
not limited to, `DREAM Challenges`_. Its main purpose is to ease the process
of creating, monitoring, and ending a challenge, as well as provide useful
functions for post-competition analysis.

.. image:: static/challenge.png
    :alt: Sample challenge page on Synapse

**challengeutils** is written in Python and uses the synapseclient_ library to
pull information from Synapse (account required).

.. _Synapse: https://www.synapse.org/
.. _DREAM Challenges: http://dreamchallenges.org/
.. _synapseclient: https://python-docs.synapse.org/build/html/index.html

Installation
============
To install from pypi:

.. code:: console

    $ pip install challengeutils

To install from the source:

.. code:: console

    $ python setup.py install

.. Attention:: 

    ``synapseclient <2.0.0`` is no longer supported, so some features may
    break if you are not on the latest client.

Contributing
============
Interested in contributing? **Awesome!** We follow the typical `GitHub workflow`_
of forking a repo, creating a branch, and opening pull requests. For more
information on how you can add or propose a change, visit our `contributing guide`_.

.. _Github workflow: https://guides.github.com/introduction/flow/
.. _contributing guide: https://github.com/Sage-Bionetworks/challengeutils/blob/master/CONTRIBUTING.md