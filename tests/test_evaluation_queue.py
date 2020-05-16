"""Tests evaluation queue helpers"""
import random
from unittest import mock
from unittest.mock import patch
import uuid

import pandas as pd
import pytest
import synapseclient

import challengeutils.utils
from challengeutils import evaluation_queue
from challengeutils.evaluation_queue import (join_evaluations,
                                             JoinFilterAnnotateQueues)

SYN = mock.create_autospec(synapseclient.Synapse)
QUEUE1 = '2'
QUEUE2 = '3'
RAND = pd.DataFrame({'objectId_x': ['123', '234']})
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
    test_dict = [{'objectId_x': '123',
                  'bar': '2222',
                  'baz': '3333'},
                 {'objectId_x': '234',
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
    test_dict = [{'objectId_x': '123',
                  'bar': '2222',
                  'baz': '3333'},
                 {'objectId_x': '234',
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


def test_keys__convert_date_to_epoch():
    """Test that the right keys are returned and right types are returned"""
    date_string = "2020-02-21T15:00:00"
    epoch_info = evaluation_queue._convert_date_to_epoch(date_string)
    assert "time_string" in epoch_info and "epochtime_ms" in epoch_info
    assert epoch_info['time_string'].endswith(".000Z")
    assert isinstance(epoch_info['epochtime_ms'], int)


def test_raiseerrors_submissionquota():
    """Tests that errors are raised when wrong parameters are passed in"""
    with pytest.raises(ValueError,
                       match="Can only specify round_end or round_duration"):
        evaluation_queue._create_quota(round_end="foo", round_duration="")

    with pytest.raises(ValueError,
                       match="If round_end is specified, "
                             "round_start must also be specified"):
        evaluation_queue._create_quota(round_end="foo")


def test_calculateduration_submissionquota():
    """Tests that calculation of round duration works"""
    first = random.randint(0, 200000)
    second = random.randint(300000, 4000000)
    first_time = str(uuid.uuid1())

    with patch.object(evaluation_queue,
                      "_convert_date_to_epoch",
                      side_effect=[{"time_string": first_time,
                                    "epochtime_ms": first},
                                   {"time_string": "doo",
                                    "epochtime_ms": second}]):
        quota = evaluation_queue._create_quota(round_start="2020-02-21T15:00:00",  # noqa pylint: disable=line-too-long
                                               round_end="2020-02-21T17:00:00")
        assert quota.firstRoundStart == first_time
        assert quota.roundDurationMillis == second - first


def test_negativeduration_submissionquota():
    """Tests that a negative duration will raise an error"""
    first = random.randint(300000, 4000000)
    second = random.randint(0, 200000)
    first_time = str(uuid.uuid1())

    with patch.object(evaluation_queue,
                      "_convert_date_to_epoch",
                      side_effect=[{"time_string": first_time,
                                    "epochtime_ms": first},
                                   {"time_string": "doo",
                                    "epochtime_ms": second}]),\
         pytest.raises(ValueError,
                       match="Specified round_duration must be >= 0, or "
                             "round_end must be > round_start"):
        evaluation_queue._create_quota(round_start="2020-02-21T15:00:00",
                                       round_end="2020-02-21T17:00:00")

    with pytest.raises(ValueError,
                       match="Specified round_duration must be >= 0, or "
                             "round_end must be > round_start"):
        evaluation_queue._create_quota(round_duration=-2)


def test_run_set_evaluation_quota():
    """Tests that a quota is set"""
    sub = random.randint(0, 4000000)
    evalid = str(uuid.uuid1())
    name = str(uuid.uuid1())
    test_eval = synapseclient.Evaluation(name=name, contentSource="syn1234")
    final_eval = synapseclient.Evaluation(name=name, contentSource="syn1234",
                                          quota={"submissionLimit": sub,
                                                 "numberOfRounds": None,
                                                 "roundDurationMillis": None,
                                                 "firstRoundStart": None})

    with patch.object(SYN, "getEvaluation",
                      return_value=test_eval) as patch_geteval,\
         patch.object(SYN, "store", return_value=final_eval) as patch_store:
        queue = evaluation_queue.set_evaluation_quota(SYN, evalid,
                                                      submission_limit=sub)
        assert queue == final_eval
        patch_store.assert_called_once_with(final_eval)
        patch_geteval.assert_called_once_with(evalid)
