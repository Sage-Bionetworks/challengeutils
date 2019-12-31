"""Test create challenge"""
import mock
from mock import patch
import uuid

import synapseclient

from challengeutils import createchallenge

SYN = mock.create_autospec(synapseclient.Synapse)


def test_create_project():
    """Test creating project"""
    name = str(uuid.uuid1())
    proj = synapseclient.Project(name, id="syn1234")
    with patch.object(SYN, "store", return_value=proj) as patch_store:
        new_proj = createchallenge.create_project(SYN, proj.name)
        assert new_proj == proj
        patch_store.assert_called_once()

def test_create_evaluation_queue():
    """Tests creating evaluation queue"""
    name = str(uuid.uuid1())
    description = str(uuid.uuid1())
    parentid = "syn12356"
    evalid = str(uuid.uuid1())
    queue = synapseclient.Evaluation(name=name,
                                     description=description,
                                     contentSource=parentid,
                                     id=evalid)
    with patch.object(SYN, "store", return_value=queue) as patch_store:
        myqueue = createchallenge.create_evaluation_queue(SYN, name,
                                                          description,
                                                          parentid)
        assert myqueue == queue
        patch_store.assert_called_once()
