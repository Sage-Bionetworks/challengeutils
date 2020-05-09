"""Tests evaluation queue helpers"""
import random
from unittest import mock
from unittest.mock import patch
import uuid

import pytest
import synapseclient

from challengeutils import evaluation_queue

SYN = mock.create_autospec(synapseclient.Synapse)


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
