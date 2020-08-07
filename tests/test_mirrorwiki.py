"""Test mirrorwiki"""
from unittest import mock
from unittest.mock import patch

import pytest
from synapseclient import Project, Wiki, Synapse
from synapseclient.core.exceptions import SynapseHTTPError
import synapseutils

from challengeutils import mirrorwiki


class TestMirrorWiki:
    """Tests mirroring wiki"""

    def setup(self):
        """Setting up all variables for tests"""
        self.markdown = "test\nsyn123/wiki/2222\nsyn123%2Fwiki%2F2222\nsyn123"
        self.wiki_mapping = {'2222': '5555'}
        self.entity = Project(name="foo", id="syn123")
        self.destination = Project(name="test", id="syn555")
        self.expected_markdown = (
            "test\nsyn555/wiki/5555\nsyn555%2Fwiki%2F5555\nsyn555"
        )
        self.syn = mock.create_autospec(Synapse)
        self.entity_wiki = Wiki(markdown=self.markdown, id="2222",
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
        # wiki page mapping {'title': Wiki}
        self.entity_wiki_pages = {'test': self.entity_wiki}
        self.destination_wiki_pages = {'test': self.entity_wiki}

        # wiki headers
        self.entity_wiki_headers = [{"id": "2222", "title": "test"}]
        self.destination_wiki_headers = [{"id": "5555", "title": "test"}]

    def test__replace_wiki_text(self):
        """Tests replacing of wiki text"""
        new_markdown = mirrorwiki._replace_wiki_text(
            markdown=self.markdown,
            wiki_mapping=self.wiki_mapping,
            entity=self.entity,
            destination=self.destination
        )
        assert new_markdown == self.expected_markdown

    def test__copy_attachments(self):
        """Test copying attachments. Test preview filehandles aren't copied"""
        get_filehandle_calls = [mock.call("322", self.entity_wiki.id,
                                          objectType='WikiAttachment'),
                                mock.call("333", self.entity_wiki.id,
                                          objectType='WikiAttachment')]
        with patch.object(self.syn, "_getFileHandleDownload",
                          side_effect=self.filehandles) as patch_get_handle,\
             patch.object(synapseutils, "copyFileHandles",
                          return_value=self.new_filehandle) as patch_copy:
            attachments = mirrorwiki._copy_attachments(self.syn,
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

    def test__copy_attachments_none(self):
        """Test no attachments are returned when there are no attachments"""
        self.entity_wiki.attachmentFileHandleIds = []
        attachments = mirrorwiki._copy_attachments(self.syn,
                                                   self.entity_wiki)
        assert attachments == []

    def test__get_headers(self):
        """Test getting headers"""
        with patch.object(self.syn, "getWikiHeaders",
                          return_value="test") as patch_get:
            headers = mirrorwiki._get_headers(self.syn, self.entity)
            assert headers == "test"
            patch_get.assert_called_once_with(self.entity)

    def test__get_headers_raiseerror(self):
        """Test correct error is raised"""
        with patch.object(self.syn, "getWikiHeaders",
                          side_effect=SynapseHTTPError),\
             pytest.raises(ValueError,
                           match="foo has no Wiki. Mirroring wikis "
                                 "require that both `entity` .*"):
            mirrorwiki._get_headers(self.syn, self.entity)

    def test__update_wiki_no_title(self):
        """Test that nothing is updated when title doesnt exist in
        destination
        """
        mirrored = mirrorwiki._update_wiki(self.syn, self.entity_wiki_pages,
                                           {'dne': "foo"})
        assert mirrored == []

    def test__update_wiki_samemarkdown_force(self):
        """Test that page is updated when markdown is the same between
        entity and destination with force=True
        """
        with patch.object(mirrorwiki, "_replace_wiki_text",
                          return_value=self.markdown),\
             patch.object(mirrorwiki, "_copy_attachments",
                          return_value=[]),\
             patch.object(self.syn, "store"):
            mirrored = mirrorwiki._update_wiki(self.syn,
                                               self.entity_wiki_pages,
                                               self.destination_wiki_pages,
                                               entity=self.entity,
                                               destination=self.destination,
                                               wiki_mapping=self.wiki_mapping,
                                               force=True)
            assert mirrored == [self.entity_wiki]

    def test__update_wiki_samemarkdown(self):
        """Test that nothing is updated when markdown is the same between
        entity and destination
        """
        with patch.object(mirrorwiki, "_replace_wiki_text",
                          return_value=self.markdown),\
             patch.object(mirrorwiki, "_copy_attachments",
                          return_value=[]):
            mirrored = mirrorwiki._update_wiki(self.syn,
                                               self.entity_wiki_pages,
                                               self.destination_wiki_pages,
                                               entity=self.entity,
                                               destination=self.destination,
                                               wiki_mapping=self.wiki_mapping)
            assert mirrored == []

    def test__update_wiki_differentmarkdown(self):
        """Test that page is updated when markdown is different between
        entity and destination
        """
        with patch.object(mirrorwiki, "_replace_wiki_text",
                          return_value=self.expected_markdown),\
             patch.object(mirrorwiki, "_copy_attachments",
                          return_value=[]),\
             patch.object(self.syn, "store"):
            mirrored = mirrorwiki._update_wiki(self.syn,
                                               self.entity_wiki_pages,
                                               self.destination_wiki_pages,
                                               entity=self.entity,
                                               destination=self.destination,
                                               wiki_mapping=self.wiki_mapping)
            assert mirrored == [self.entity_wiki]

    def test__update_wiki_dryrun(self):
        """Test that page is updated when markdown is different between
        entity and destination
        """
        with patch.object(mirrorwiki, "_replace_wiki_text",
                          return_value=self.expected_markdown),\
             patch.object(mirrorwiki, "_copy_attachments",
                          return_value=[]),\
             patch.object(self.syn, "store") as patch_store:
            mirrored = mirrorwiki._update_wiki(self.syn,
                                               self.entity_wiki_pages,
                                               self.destination_wiki_pages,
                                               entity=self.entity,
                                               destination=self.destination,
                                               wiki_mapping=self.wiki_mapping,
                                               dryrun=True)
            assert mirrored == [self.entity_wiki]
            patch_store.assert_not_called()

    def test__update_wiki_integration(self):
        """Make sure correct parameters are called"""
        with patch.object(mirrorwiki, "_replace_wiki_text",
                          return_value=self.expected_markdown) as patch_rep,\
             patch.object(mirrorwiki, "_copy_attachments",
                          return_value=[]) as patch_copy,\
             patch.object(self.syn, "store"):
            mirrored = mirrorwiki._update_wiki(self.syn,
                                               self.entity_wiki_pages,
                                               self.destination_wiki_pages,
                                               entity=self.entity,
                                               destination=self.destination,
                                               wiki_mapping=self.wiki_mapping,
                                               dryrun=True)
            patch_rep.assert_called_once_with(markdown=self.markdown,
                                              wiki_mapping=self.wiki_mapping,
                                              entity=self.entity,
                                              destination=self.destination)
            patch_copy.assert_called_once_with(self.syn, self.entity_wiki)

    def test__get_wikipages_and_mapping(self):
        """Test that page is updated when markdown is different between
        entity and destination
        """
        headers = [self.entity_wiki_headers, self.destination_wiki_headers]
        wikis = [self.entity_wiki, self.entity_wiki]
        with patch.object(mirrorwiki, "_get_headers",
                          side_effect=headers),\
             patch.object(self.syn, "getWiki", side_effect=wikis):
            wiki_dict = mirrorwiki._get_wikipages_and_mapping(
                self.syn, self.entity, self.destination
            )
            print(wiki_dict['destination_wiki_pages'])
        assert wiki_dict == {'entity_wiki_pages': self.entity_wiki_pages,
                             'destination_wiki_pages': self.entity_wiki_pages,
                             'wiki_mapping': self.wiki_mapping}

    def test__get_wikipages_and_mapping_none(self):
        """Test that wiki pages that exist in the destination also exist
        in the old page
        """
        headers = [[], self.destination_wiki_headers]
        with patch.object(mirrorwiki, "_get_headers",
                          side_effect=headers),\
             patch.object(self.syn, "getWiki",
                          return_value=self.entity_wiki):
            wiki_dict = mirrorwiki._get_wikipages_and_mapping(
                self.syn, self.entity, self.destination
            )
        assert wiki_dict == {'entity_wiki_pages': {},
                             'destination_wiki_pages': self.entity_wiki_pages,
                             'wiki_mapping': {}}

    def test__get_wikipages_and_mapping_integration(self):
        """Integration test: make sure right parameters are callled
        """
        get_header_calls = [mock.call(self.syn, self.entity),
                            mock.call(self.syn, self.destination)]
        get_wiki_calls = [mock.call(self.entity, '2222'),
                          mock.call(self.destination, '5555')]
        headers = [self.entity_wiki_headers, self.destination_wiki_headers]
        wikis = [self.entity_wiki, self.entity_wiki]
        with patch.object(mirrorwiki, "_get_headers",
                          side_effect=headers) as patch_get_headers,\
             patch.object(self.syn, "getWiki",
                          side_effect=wikis) as patch_wiki:
            wiki_dict = mirrorwiki._get_wikipages_and_mapping(
                self.syn, self.entity, self.destination
            )
            patch_get_headers.assert_has_calls(get_header_calls)
            patch_wiki.assert_has_calls(get_wiki_calls)

    def test_mirror(self):
        """Integration test: Tests all parameters are called correctly"""
        entities = [self.entity, self.destination]
        mappings = {'entity_wiki_pages': self.entity_wiki_pages,
                    'destination_wiki_pages': self.entity_wiki_pages,
                    'wiki_mapping': self.wiki_mapping}
        get_calls = [mock.call(self.entity, downloadFile=False),
                     mock.call(self.destination, downloadFile=False)]
        with patch.object(self.syn, "get",
                          side_effect=entities) as patch_get,\
             patch.object(mirrorwiki, "_get_wikipages_and_mapping",
                          return_value=mappings) as patch_get_mapping,\
             patch.object(mirrorwiki, "_update_wiki") as patch_update:
            mirrorwiki.mirror(self.syn, entity=self.entity,
                              destination=self.destination,
                              force=True, dryrun=True)
            patch_get.assert_has_calls(get_calls)
            patch_get_mapping.assert_called_once_with(self.syn, self.entity,
                                                      self.destination)
            patch_update.assert_called_once_with(self.syn, **mappings,
                                                 force=True, dryrun=True,
                                                 entity=self.entity,
                                                 destination=self.destination)
