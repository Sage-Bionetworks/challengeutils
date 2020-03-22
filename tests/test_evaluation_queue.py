import mock
from mock import patch
import pandas as pd
import synapseclient

import challengeutils.utils
from challengeutils.evaluation_queue import join_evaluations

SYN = mock.create_autospec(synapseclient.Synapse)


def test_join_queues():
    """Archive and attach writeups"""
    writeups = [{"submitterId": '123',
                 'objectId': '2222'},
                {"submitterId": '234',
                 'objectId': '5555'}]

    submissions = [{"submitterId": '123',
                    'objectId': '3333'},
                   {"submitterId": '234',
                    'objectId': '4444'}]

    firstquery = "select * from evaluation_2"
    secondquery = "select * from evaluation_3"
    expected_dict = [{'submitterId': '123',
                      'objectId_x': '2222',
                      'objectId_y': '3333'},
                     {'submitterId': '234',
                      'objectId_x': '5555',
                      'objectId_y': '4444'}]
    expecteddf = pd.DataFrame(expected_dict)
    with patch.object(challengeutils.utils,
                      "evaluation_queue_query",
                      side_effect=[writeups,
                                   submissions]) as patch_query:
        joineddf = join_evaluations(SYN, '2', '3', "submitterId")
        calls = [mock.call(SYN, firstquery), mock.call(SYN, secondquery)]
        patch_query.assert_has_calls(calls)
        assert joineddf.equals(expecteddf[joineddf.columns])