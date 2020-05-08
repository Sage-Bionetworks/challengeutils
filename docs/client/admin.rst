.. _challengeutils-admin-cmd:

***********************
Admin Built-in Commands
***********************

The following commands must be ran with ``challengeutils``, e.g.

.. code:: console

    $ challengeutils <built-in command> <options>

-------


Create a challenge
------------------

Synopsis
^^^^^^^^

createchallenge
    "CHALLENGE NAME HERE" [--livesiteid ]

Description
^^^^^^^^^^^

Create a challenge space in Synapse, including two Projects and
four Teams that are needed for a challenge. For more information
on various Challenge components, see `challenge administration`_.

.. _challenge administration: https://docs.synapse.org/articles/challenge_administration.html

Options
^^^^^^^

.. program:: challengeutils createchallenge

.. cmdoption:: --livesiteid

    Overwrite an existing live site

-------


Mirror wiki changes
-------------------

Synopsis
^^^^^^^^

mirrorwiki
    source_id dest_id [--forceupdate]

Description
^^^^^^^^^^^

Sync changes made from a source wiki to the destination wiki, e.g. from staging
to live. Updates will only occur in wiki pages that have matching titles in the
source wiki.

.. Important::

    This command is different from copying wikis. To copy, see synapseutils_.

For best practice, **make all edits to the staging site of a challenge only**,
then use this command to sync over the changes to the live site.

.. _synapseutils: https://python-docs.synapse.org/build/html/synapseutils.html


Options
^^^^^^^

.. program:: challengeutils mirrorwiki

.. cmdoption:: --forceupdate

    Force-update the wiki pages, even if there are no changes

-------


List evaluations
----------------

Synopsis
^^^^^^^^

listevaluations
    projectid

Description
^^^^^^^^^^^

List all evaluation queues of a Synapse project

-------


Set an evaluation quota
-----------------------

Synopsis
^^^^^^^^

setevaluationquota
    evalid [--round_start yyyy-MM-ddTHH:mm:ss 
    [--round_end yyyy-MM-ddTHH:mm:ss]
    [--round_duration n]
    [--num_rounds n] [--sub_limit n]

Description
^^^^^^^^^^^

Set the quota of an evaluation queue

.. Warning::

    This **will** erase all settings previously set for the queue,
    unless otherwise specified by the parameters when you run this
    command.

Options
^^^^^^^

.. program:: challengeutils setevaluationquota

.. cmdoption:: --round_start

    Start of round in yyyy-MM-ddTHH:mm:ss (local military time) format

.. cmdoption:: --round_end

    End of round in yyyy-MM-ddTHH:mm:ss (local military time) format;
    do not use with ``round_duration``

.. cmdoption:: --round_duration

    Round duration in milliseconds; do not use with ``round_end``

.. cmdoption:: --num_rounds

    Number of rounds (must set for time-related quotas to work)

.. cmdoption:: --sub_limit

    Number of submissions allowed per round

-------


Update an evaluation ACL
------------------------

Synopsis
^^^^^^^^

setevaluationacl
    evalid user_or_team permission_level

Description
^^^^^^^^^^^

Set the evaluation permissions for ``user_or_team`` with 
``permission_level`` access.

-------


Query an evaluation
-------------------

Synopsis
^^^^^^^^

query
    "QUERY" [--outputfile file] [--render] 
    [--limit n] [--offset n]

Description
^^^^^^^^^^^

Query an evaluation queue

Options
^^^^^^^

.. program:: challengeutils query

.. cmdoption:: --outputfile file

    Print query results to this file (default: prints to ``stdout``)

.. cmdoption:: --render

    Render submitterId and createdOn values in leaderboard

.. cmdoption:: --limit 20

    Only return this number of results (default: 20)

.. cmdoption:: --offset 0

    Return results starting at this offset (default: 0)

-------


Download a submission
---------------------

Synopsis
^^^^^^^^

downloadsubmission
    subid [--download_location path] [--output file]

Description
^^^^^^^^^^^

Download a Submission object

Options
^^^^^^^

.. program:: challengeutils downloadsubmission

.. cmdoption:: --download_location path

    Specify download location (default: current working directory)

.. cmdoption:: --output file

    Print JSON results to this file (default: prints to ``stdout``)

-------


Annotate a submission
---------------------

Synopsis
^^^^^^^^

annotatesubmission
    synid json_file [--to_public ]

Description
^^^^^^^^^^^

foo

Options
^^^^^^^

.. program:: challengeutils annotatesubmission

.. cmdoption:: --help, -h

    Show help message and exit


-------

Update a submission status
--------------------------

Synopsis
^^^^^^^^

changestatus
    synid json_file [--to_public ]

Description
^^^^^^^^^^^

foo

Options
^^^^^^^

.. program:: challengeutils changestatus

.. cmdoption:: --help, -h

    Show help message and exit

-------


Stop a Docker submission
------------------------

Synopsis
^^^^^^^^

killdockeroverquota
    synid json_file [--to_public ]

Description
^^^^^^^^^^^

foo

Options
^^^^^^^

.. program:: challengeutils killdockeroverquota

.. cmdoption:: --help, -h

    Show help message and exit

-------


Update an entity ACL
--------------------

Synopsis
^^^^^^^^

setentityacl
    synid json_file [--to_public ]

Description
^^^^^^^^^^^

foo

Options
^^^^^^^

.. program:: challengeutils setentityacl

.. cmdoption:: --help, -h

    Show help message and exit

