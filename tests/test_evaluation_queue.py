"""Tests evaluation queue helpers"""
import time

from mock import patch

from challengeutils import evaluation_queue


def test_keys__convert_date_to_epoch():
    """Test that the right keys are returned"""
    date_string = "2020-02-21T15:00:00"
    epoch_info = evaluation_queue._convert_date_to_epoch(date_string)
    assert "time_string" in epoch_info and "epochtime_ms" in epoch_info
    assert epoch_info['time_string'].endswith(".000Z")
    assert isinstance(epoch_info['epochtime_ms'], int)

    