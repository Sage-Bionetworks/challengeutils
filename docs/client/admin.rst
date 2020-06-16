.. _challengeutils-admin-cmd:

***********************
Admin Built-in Commands
***********************

The following commands must be ran with ``challengeutils``, e.g.

.. code:: console

    $ challengeutils <built-in command> <options>

Note that the majority of the commands listed here will require certain
permissions on the relevant Sypanse entities, e.g. ``admin`` permissions
or ``score`` permissions.

For more information on Synapse permissions, see here_.

.. _here: https://docs.synapse.org/articles/sharing_settings.html#sharing-settings

-------


Create a challenge
------------------

Synopsis
^^^^^^^^

createchallenge
    "CHALLENGE NAME HERE" [--livesiteid SYNID]

Description
^^^^^^^^^^^

Create a challenge space in Synapse, including two Projects and
four Teams that are needed for a challenge. For more information
on various Challenge components, see `challenge administration`_.

.. _challenge administration: https://docs.synapse.org/articles/challenge_administration.html

Positional
^^^^^^^^^^

.. program:: challengeutils createchallenge

.. cmdoption:: "CHALLENGE NAME HERE"

    Name of the challenge

Optional
^^^^^^^^

.. cmdoption:: --livesiteid SYNID

    Overwrite an existing live site

-------


Mirror wiki changes
-------------------

Synopsis
^^^^^^^^

mirrorwiki
    source_id dest_id [--force]

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


Positional
^^^^^^^^^^

.. program:: challengeutils mirrorwiki

.. cmdoption:: source_id

    Synpase ID of the source wiki to be synced

.. cmdoption:: dest_id

    Synapse ID of the destination wiki to be synced to

Optional
^^^^^^^^

.. cmdoption:: -f, --force

    Force-update the wiki pages, even if there are no changes

-------


List evaluations
----------------

Synopsis
^^^^^^^^

listevaluations
    project_id

Description
^^^^^^^^^^^

List all evaluation queues of a Synapse project.

Positional
^^^^^^^^^^

.. program:: challengeutils listevaluations

.. cmdoption:: project_id

    Project ID on Synapse, e.g. ``syn12345678``

-------


Set an evaluation quota
-----------------------

Synopsis
^^^^^^^^

setevaluationquota
    eval_id [--round_start yyyy-MM-ddTHH:mm:ss 
    [--round_end yyyy-MM-ddTHH:mm:ss]
    [--round_duration n]
    [--num_rounds n] [--sub_limit n]

Description
^^^^^^^^^^^

Set the quota of an evaluation queue. Quota options include the round
starting date, round ending date, round duration, number of rounds, and 
submission limit.

.. Warning::

    When this command is used, **all settings previously set for the queue
    will be erased**. For any settings you do not want to update or remove,
    pass the original values into the optional parameters defined below.

Positional
^^^^^^^^^^

.. program:: challengeutils setevaluationquota

.. cmdoption:: eval_id

    Evaluation ID on Synapse, e.g. ``9876543``

Optional
^^^^^^^^

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

Positional
^^^^^^^^^^

.. program:: challengeutils setevaluationquota

.. cmdoption:: eval_id

    Evaluation ID on Synapse, e.g. ``9876543``

.. cmdoption:: user_or_team

    Synapse user or team ID, e.g. ``1234567``

.. cmdoption:: permission_level

    One of: ``view``, ``submit``, ``score``, ``admin``, ``remove``

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

Query an evaluation queue.

Positional
^^^^^^^^^^

.. program:: challengeutils query

.. cmdoption:: "QUERY"

    SQL-like query in URI format

Optional
^^^^^^^^

.. cmdoption:: --outputfile file

    Print query results to this file (default: prints to ``stdout``)

.. cmdoption:: --render

    Render ``submitterId`` and ``createdOn`` values in leaderboard

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
    sub_id [--download_location path] [--output file]

Description
^^^^^^^^^^^

Download a Submission object.

Positional
^^^^^^^^^^

.. program:: challengeutils downloadsubmission

.. cmdoption:: sub_id

    Submission ID on Synapse, e.g. ``9876543``

Optional
^^^^^^^^

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
    sub_id json_file [-p ] [-f]

Description
^^^^^^^^^^^

Annotate a Submission object with a JSON file.  The file should comprise of
a list of key-value pairs, where the key is the annotation and the value is
the annotation value, e.g.

.. code:: json

    {
        "round": 1,
        "score": 100
    }

Positional
^^^^^^^^^^

.. program:: challengeutils annotatesubmission

.. cmdoption:: sub_id

    Submission ID on Synapse, e.g. ``9876543``

.. cmdoption:: json_file

    Filepath to the JSON file containing the annotations

Optional
^^^^^^^^

.. cmdoption:: -p, --to_public

    Allow the annotation to be viewable by the public (default: annotation
    is viewable by the queue administrator(s) only)

.. cmdoption:: -f, --force

    Force the update, even if the key has a different ACL


-------

Update a submission status
--------------------------

Synopsis
^^^^^^^^

changestatus
    sub_id status

Description
^^^^^^^^^^^

Update the ``status`` annotation of a Submission Status object.

Positional
^^^^^^^^^^

.. program:: challengeutils changestatus

.. cmdoption:: sub_id

    Submission ID on Synapse, e.g. ``9876543``

.. cmdoption:: status

    One of: ``RECEIVED``, ``ACCEPTED``, ``INVALID``, ``VALIDATED``, 
    ``SCORED``, ``OPEN``, ``CLOSED``, ``EVALUATION_IN_PROGRESS``,
    ``REJECTED``

-------


Stop a Docker submission
------------------------

Synopsis
^^^^^^^^

killdockeroverquota
    eval_id time_quota

Description
^^^^^^^^^^^

Terminate a Docker submission (usually applies to submissions that have a
runtime longer than the alloted time).

Positional
^^^^^^^^^^

.. program:: challengeutils killdockeroverquota

.. cmdoption:: eval_id

    Evaluation ID on Synapse, e.g. ``9876543``

.. cmdoption:: time_quota

    Time quota in milliseconds allowed for a submission

-------


Update an entity ACL
--------------------

Synopsis
^^^^^^^^

setentityacl
    ent_id user_or_team permission_level

Description
^^^^^^^^^^^

Set the entity permissions for ``user_or_team`` with 
``permission_level`` access.

Positional
^^^^^^^^^^

.. program:: challengeutils setentityacl

.. cmdoption:: ent_id

    Entity ID on Synapse, e.g. ``syn12345678``

.. cmdoption:: user_or_team

    Synapse user or team ID, e.g. ``1234567``

.. cmdoption:: permission_level

    One of: ``view``, ``submit``, ``score``, ``admin``, ``remove``

-------


Validate a Project Submission
-----------------------------

Synopsis
^^^^^^^^

validate-project
    submissionid challengewiki permission_level [-p] [-a] [-o]

Description
^^^^^^^^^^^

Validates a Synapse Project submission by making sure it is shared with the
correct users.

Positional
^^^^^^^^^^

.. program:: challengeutils validate-project

.. cmdoption:: submissionid

    Submission ID on Synapse, e.g. ``9876543``

.. cmdoption:: challengewiki

    Synapse ID of challenge project

Optional
^^^^^^^^

.. cmdoption:: -p, --public

    Check that the Project is shared with the public

.. cmdoption:: -a, --admin

    Check that the Project is shared with this admin username/team

.. cmdoption:: -o, --output

    Output the validation results into a json file


-------


Archive a Project Submission
----------------------------

Synopsis
^^^^^^^^

archive-project
    submissionid admin [-o]

Description
^^^^^^^^^^^

Archives a Project submission by copying it

Positional
^^^^^^^^^^

.. program:: challengeutils archive-project

.. cmdoption:: submissionid

    Submission ID on Synapse, e.g. ``9876543``

.. cmdoption:: admin

    Synapse ID of user or team

Optional
^^^^^^^^

.. cmdoption:: -o, --output

    Output the results into a json file

-------

Delete a submission
-------------------

Synopsis
^^^^^^^^

delete-submission
    sub_id

Description
^^^^^^^^^^^

Delete a submission

Positional
^^^^^^^^^^

.. program:: challengeutils delete-submission

.. cmdoption:: sub_id

    Submission ID on Synapse, e.g. ``9876543``
