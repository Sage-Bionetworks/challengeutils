.. _challengeutils-part-cmd:

*****************************
Participant Built-in Commands
*****************************

The following commands must be ran with ``challengeutils``, e.g.

.. code:: console

    $ challengeutils <built-in command> <options>

-------


List challenges
---------------

Synopsis
^^^^^^^^

list-registered-challenges
    [--userid USER]

Description
^^^^^^^^^^^

List all challenges to which the user is registered. Defaults to the
Synapse user currently logged in if USER is not specified.

Options
^^^^^^^

.. program:: challengeutils list-registered-challenges

.. cmdoption:: --userid USER

    Synapse user ID or username