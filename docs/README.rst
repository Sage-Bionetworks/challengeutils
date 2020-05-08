**************
challengeutils
**************

.. image:: https://img.shields.io/docker/automated/sagebionetworks/challengeutils
    :target: https://hub.docker.com/r/sagebionetworks/challengeutils/
    :alt: Docker build automation

.. image:: https://img.shields.io/pypi/v/challengeutils
    :target: https://pypi.python.org/pypi/challengeutils
    :alt: PyPI version

.. image:: https://travis-ci.org/Sage-Bionetworks/challengeutils.svg?branch=develop
    :target: https://travis-ci.org/Sage-Bionetworks/challengeutils
    :alt: Build status

This package provides an interface for managing Sage Bionetworks Challenges 
administered using Synapse_, including `DREAM Challenges`_. This package is
being actively developed and maintained by DREAM and Informatics & Biocomputing
(IBC), Computational Oncology Group at Sage Bionetworks.

.. _Synapse: https://www.synapse.org/
.. _DREAM Challenges: http://dreamchallenges.org/

Installation
============
To install from pypi:

.. code:: console

    $ pip install challengeutils

To install from the source:

.. code:: console

    $ python setup.py install

.. Attention:: synapseclient <2.0.0 is no longer supported, so some features may break if you are not on the latest client.

Contributing
============
If you would like to propose a change to challengeutils, you can find more information
on contributing in our `contributing guide`_ on GitHub.

.. _contributing guide: https://github.com/Sage-Bionetworks/challengeutils#contributing