import uuid

import mock
from mock import patch
import pandas as pd
import synapseclient

import challengeutils.utils
from challengeutils.evaluation_queue import join_evaluations
from challengeutils.evaluation_queue import JoinFilterAnnotateQueues

SYN = mock.create_autospec(synapseclient.Synapse)
QUEUE1 = '2'
QUEUE2 = '3'
RAND = str(uuid.uuid1())
JOIN = str(uuid.uuid1())


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


class JoinTestClass(JoinFilterAnnotateQueues):
    def filter(self, joineddf):
        return RAND


def test_calls_joinfilterannotate():
    """Test correct calls are made with each function"""
    test_dict = [{'foo': '123',
                  'bar': '2222',
                  'baz': '3333'},
                 {'foo': '234',
                  'bar': '5555',
                  'baz': '4444'}]
    test_dict = pd.DataFrame(test_dict)
    joinby = str(uuid.uuid1())
    how = 'left'
    testcls = JoinTestClass(SYN, queue1=QUEUE1, queue2=QUEUE2, joinby=joinby,
                            how=how)
    with patch.object(JoinTestClass, "join",
                      return_value=JOIN) as patch_join,\
         patch.object(JoinTestClass, "filter",
                      return_value=RAND) as patch_filter,\
         patch.object(JoinTestClass, "annotate") as patch_annotate:
        testcls()
        patch_join.assert_called_once_with(joinby=joinby, how=how)
        patch_filter.assert_called_once_with(JOIN)
        patch_annotate.assert_called_once_with(RAND)



def test_filter_joinfilterannotate():
    """Test filter returns the correct call"""
    test_dict = [{'foo': '123',
                  'bar': '2222',
                  'baz': '3333'},
                 {'foo': '234',
                  'bar': '5555',
                  'baz': '4444'}]
    test_dict = pd.DataFrame(test_dict)


    with patch.object(JoinTestClass, "join",
                      return_value=JOIN) as patch_join,\
         patch.object(JoinTestClass, "annotate") as patch_annotate:
        testcls.join()
        patch_join.assert_called_once()
        patch_annotate.assert_called_once_with(RAND)


def test_filter_joinfilterannotate():
    """Test filter returns the correct call"""
    test_dict = [{'foo': '123',
                  'bar': '2222',
                  'baz': '3333'},
                 {'foo': '234',
                  'bar': '5555',
                  'baz': '4444'}]
    test_dict = pd.DataFrame(test_dict)
    with patch.object(JoinTestClass, "join",
                      return_value=JOIN) as patch_join,\
         patch.object(JoinTestClass, "annotate") as patch_annotate:
        testcls = JoinTestClass(SYN, queue1=QUEUE1, queue2=QUEUE2)
        testcls()
        patch_join.assert_called_once()
        patch_annotate.assert_called_once_with(RAND)


def test_annotate_joinfilterannotate():
    """Test filter returns the correct call"""
    objectid = str(uuid.uuid1())
    keys = ['bar', 'baz']
    rand1 = str(uuid.uuid1())
    rand2 = str(uuid.uuid1())
    test_dict = [{'objectId_x': objectid,
                  'bar': rand1,
                  'baz': rand2}]
    testdf = pd.DataFrame(test_dict)
    testcls = JoinTestClass(SYN, queue1=QUEUE1, queue2=QUEUE2,
                            keys=keys)
    with patch.object(challengeutils.utils,
                      "annotate_submission") as patch_annotate:
        testcls.annotate(testdf)
        patch_annotate.assert_called_once_with(SYN, objectid,
                                               testdf.iloc[0][keys].to_dict(),
                                               keys)
