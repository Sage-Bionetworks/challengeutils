"""Tests challengeutils.cheat-detection functions"""
# pylint: disable=line-too-long
from unittest.mock import Mock, patch
import uuid

import pytest
import requests
import synapseclient

from challengeutils import cheat_detection

SYN = synapseclient.Synapse()

class TestCheatDetection:
    def setup(self):
        """Setup test"""
        
        self.cheat_detection_obj = cheat_detection.CheatDetection(
            syn=SYN,
            evaluation_id="123456"
        )
        

    def test_string_representation(self):
        "Tests string representation of Cheat Detection"
        assert str(self.cheat_detection_obj) == """
Evaluation ID: 123456
Accepted Submissions: 0
Potentially Linked Users: 0
        """
    
    def test_evaluation_id(self):
        "Test that the evaluation id is valid"
        eval = self.syn.getEvaluation()

    def test_representation(self):
        "Tests the representation of the CheatDetection Object"
        assert repr(self.cheat_detection_obj) == f"CheatDetection({self.cheat_detection_obj.syn}, 123456)"


    def test_get_number_of_linked_users(self):
        "Tests that the number of linked users is correct"
        num = len(self.cheat_detection_obj.linked_users)
        assert self.cheat_detection_obj.get_number_of_linked_users() == num