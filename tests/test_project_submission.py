"""Testing writeup attacher"""
import mock

import pandas as pd
import synapseclient

from challengeutils.project_submission import JoinWriteupChallengeQueues

SYN = mock.create_autospec(synapseclient.Synapse)
WRITEUP_QUEUEID = '2'
SUBMISSION_QUEUEID = '3'
JOIN_CLS = JoinWriteupChallengeQueues(SYN, WRITEUP_QUEUEID,
                                      SUBMISSION_QUEUEID)


def test_join_writeup_queue_no_filters():
    """Tests when no filters are done"""
    input_dict = [{'submitterId': '123',
                   'status_y': 'VALIDATED',
                   'status_x': 'SCORED',
                   'entityId_y': 'syn1234',
                   'archived': 'syn3333',
                   'objectId_x': '2222',
                   'objectId_y': '3333'},
                  {'submitterId': '234',
                   'status_y': 'VALIDATED',
                   'status_x': 'SCORED',
                   'entityId_y': 'syn2333',
                   'archived': 'syn4444',
                   'objectId_x': '5555',
                   'objectId_y': '4444'}]
    inputdf = pd.DataFrame(input_dict)

    expected_dict = [{'submitterId': '123',
                      'status_y': 'VALIDATED',
                      'status_x': 'SCORED',
                      'writeUp': 'syn1234',
                      'archivedWriteUp': 'syn3333',
                      'objectId_x': '2222',
                      'objectId_y': '3333'},
                     {'submitterId': '234',
                      'status_y': 'VALIDATED',
                      'status_x': 'SCORED',
                      'writeUp': 'syn2333',
                      'archivedWriteUp': 'syn4444',
                      'objectId_x': '5555',
                      'objectId_y': '4444'}]
    expecteddf = pd.DataFrame(expected_dict)

    assert JOIN_CLS._status_key == "status"
    filtereddf = JOIN_CLS.filter(inputdf)
    # Make sure index is ordered correctly
    assert filtereddf.equals(expecteddf.loc[filtereddf.index, :])


def test_join_writeup_queue_empty():
    """Tests when there are no VALIDATED or SCORED submission"""
    input_dict = [{'submitterId': '123',
                   'status_y': 'INVALID',
                   'status_x': 'SCORED',
                   'entityId_y': 'syn1234',
                   'archived': 'syn3333',
                   'objectId_x': '2222',
                   'objectId_y': '3333'},
                  {'submitterId': '234',
                   'status_y': 'VALIDATED',
                   'status_x': 'INVALID',
                   'entityId_y': 'syn2333',
                   'archived': 'syn4444',
                   'objectId_x': '5555',
                   'objectId_y': '4444'}]
    inputdf = pd.DataFrame(input_dict)

    assert JOIN_CLS._status_key == "status"
    filtereddf = JOIN_CLS.filter(inputdf)
    assert filtereddf.empty


def test_join_writeup_queue_no_dups():
    """Tests that there are no duplicated for the first leaderboard"""
    input_dict = [{'submitterId': '123',
                   'status_y': 'VALIDATED',
                   'status_x': 'SCORED',
                   'entityId_y': 'syn1234',
                   'archived': 'syn3333',
                   'objectId_x': '2222',
                   'objectId_y': '5555'},
                  {'submitterId': '234',
                   'status_y': 'VALIDATED',
                   'status_x': 'SCORED',
                   'entityId_y': 'syn2333',
                   'archived': 'syn4444',
                   'objectId_x': '2222',
                   'objectId_y': '4444'}]
    inputdf = pd.DataFrame(input_dict)

    # Checks that higher objectId_y submission is taken
    # after dropping duplicates
    expected_dict = [{'submitterId': '123',
                      'status_y': 'VALIDATED',
                      'status_x': 'SCORED',
                      'writeUp': 'syn1234',
                      'archivedWriteUp': 'syn3333',
                      'objectId_x': '2222',
                      'objectId_y': '5555'}]
    expecteddf = pd.DataFrame(expected_dict)
    assert JOIN_CLS._status_key == "status"
    filtereddf = JOIN_CLS.filter(inputdf)
    # Make sure index is ordered correctly
    assert filtereddf.equals(expecteddf)
