"""Test mirrorwiki"""
from unittest import mock
from unittest.mock import patch

import pytest
from synapseclient import File, Folder, Project, Wiki, Synapse
try:
    from synapseclient.core.exceptions import SynapseHTTPError
except ModuleNotFoundError:
    # For synapseclient < v2.0
    from synapseclient.exceptions import SynapseHTTPError
import synapseutils

from challengeutils import mirrorwiki


class TestMirrorWiki:
    
    def setup(self):
        self.markdown = "test\nsyn123/wiki/2222\nsyn123%2Fwiki%2F2222\nsyn123"
        self.wiki_mapping = {'2222': '5555'}
        self.entity = Project(name="foo", id="syn123")
        self.destination = Project(name="test", id="syn555")
        self.expected_markdown = (
            "test\nsyn555/wiki/5555\nsyn555%2Fwiki%2F5555\nsyn555"
        )
        self.syn = mock.create_autospec(Synapse)
        self.entity_wiki = Wiki(markdown=self.markdown, id="111",
                                owner="syn123",
                                attachmentFileHandleIds=['322', '333'])
        self.filehandles = [
            {
                'fileHandle': {
                    "concreteType": mirrorwiki.PREVIEW_FILE_HANDLE,
                    "contentType": "contenttype",
                    "fileName": "name"
                }

            },
            {
                'fileHandle': {
                    "concreteType": "not_preview",
                    "contentType": "testing",
                    "fileName": "foobar"
                }

            }
        ]
        self.new_filehandle = [{'newFileHandle': {"id": "12356"}}]

    def test_replace_wiki_text(self):
        """Tests replacing of wiki text"""
        new_markdown = mirrorwiki.replace_wiki_text(
            markdown=self.markdown,
            wiki_mapping=self.wiki_mapping,
            entity=self.entity,
            destination=self.destination
        )
        assert new_markdown == self.expected_markdown
    
    def test_copy_attachments(self):
        """Test copying attachments. Test preview filehandles aren't copied"""
        get_filehandle_calls = [mock.call("322", self.entity_wiki.id,
                                          objectType='WikiAttachment'),
                                mock.call("333", self.entity_wiki.id,
                                          objectType='WikiAttachment')]
        with patch.object(self.syn, "_getFileHandleDownload",
                          side_effect=self.filehandles) as patch_get_handle,\
             patch.object(synapseutils, "copyFileHandles",
                          return_value=self.new_filehandle) as patch_copy:
            attachments = mirrorwiki.copy_attachments(self.syn,
                                                      self.entity_wiki)
            assert attachments == ["12356"]
            patch_get_handle.assert_has_calls(get_filehandle_calls)
            patch_copy.assert_called_once_with(self.syn,
                                               [{"concreteType": "not_preview",
                                                 "contentType": "testing",
                                                 "fileName": "foobar"}],
                                               ["WikiAttachment"],
                                               [self.entity_wiki.id],
                                               ['testing'],
                                               ['foobar'])

    def test_copy_attachments_none(self):
        """Test no attachments are returned when there are no attachments"""
        self.entity_wiki.attachmentFileHandleIds = []
        attachments = mirrorwiki.copy_attachments(self.syn,
                                                  self.entity_wiki)
        assert attachments == []

    def test_get_headers(self):
        """Test getting headers"""
        with patch.object(self.syn, "getWikiHeaders",
                          return_value="test") as patch_get:
            headers = mirrorwiki.get_headers(self.syn, self.entity)
            assert headers == "test"
            patch_get.assert_called_once_with(self.entity)

    def test_get_headers_raiseerror(self):
        """Test correct error is raised"""
        with patch.object(self.syn, "getWikiHeaders",
                          side_effect=SynapseHTTPError),\
             pytest.raises(ValueError,
                           match="foo has no Wiki. Mirroring wikis "
                                 "require that both `entity` .*"):
            mirrorwiki.get_headers(self.syn, self.entity)
    