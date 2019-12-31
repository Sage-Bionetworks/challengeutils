"""Test create challenge"""
import uuid

import mock
from mock import patch
import synapseclient
from synapseclient.exceptions import SynapseHTTPError

from challengeutils import createchallenge
from challengeutils import utils
from synapseservices.challenge import Challenge

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


def test_create_live_page():
    """Creates live page"""
    teamid = str(uuid.uuid1())
    project = str(uuid.uuid1())
    markdown = createchallenge.LIVE_PAGE_MARKDOWN % (teamid, teamid)
    wiki = synapseclient.Wiki(title='', owner=project,
                              markdown=markdown)
    with patch.object(SYN, "store") as patch_store:
        createchallenge.create_live_page(SYN, project, teamid)
        patch_store.assert_called_once_with(wiki)


def test_create_challenge_widget():
    """Tests creating challenge widget"""
    teamid = str(uuid.uuid1())
    project = str(uuid.uuid1())
    chalid = str(uuid.uuid1())
    etag = str(uuid.uuid1())
    challenge_obj = Challenge(id=chalid,
                              projectId=project,
                              etag=etag,
                              participantTeamId=teamid)
    with patch.object(utils, "create_challenge",
                      return_value=challenge_obj) as patch_create:
        chal = createchallenge.create_challenge_widget(SYN, project, teamid)
        assert chal == challenge_obj
        patch_create.assert_called_once_with(SYN, project, teamid)


def test_existing_create_challenge_widget():
    """Tests existing challenge widget"""
    teamid = str(uuid.uuid1())
    project = str(uuid.uuid1())
    chalid = str(uuid.uuid1())
    etag = str(uuid.uuid1())
    challenge_obj = Challenge(id=chalid,
                              projectId=project,
                              etag=etag,
                              participantTeamId=teamid)
    with patch.object(utils, "create_challenge",
                      side_effect=SynapseHTTPError) as patch_create,\
        patch.object(utils, "get_challenge",
                     return_value=challenge_obj) as patch_get:
        chal = createchallenge.create_challenge_widget(SYN, project, teamid)
        assert chal == challenge_obj
        patch_create.assert_called_once_with(SYN, project, teamid)
        patch_get.assert_called_once_with(SYN, project)