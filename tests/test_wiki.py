"""Test wiki module"""
import tempfile
from unittest import mock
from unittest.mock import patch

import synapseclient

import challengeutils.wiki


class TestWiki:
    """Test wiki"""

    def setup_method(self):
        """Method called once per method"""
        self.syn = mock.create_autospec(synapseclient.Synapse)
        self.file1 = tempfile.NamedTemporaryFile(suffix=".md")
        self.file2 = tempfile.NamedTemporaryFile(suffix=".md")
        self.wiki_config = [
            {
                "id": "1",
                "title": "Wish You Were Here",
                "markdown_path": self.file1.name
            },
            {
                "id": "2",
                "title": "Echoes",
                "parentId": "1",
                "markdown_path": self.file2.name
            }
        ]

    def teardown_method(self):
        """Method called once per method"""
        self.file1.close()
        self.file2.close()

    def test_validate_config(self):
        """Test validation config"""
        with patch.object(challengeutils.wiki, "read_wiki_config",
                          return_value=self.wiki_config) as patch_read:
            config = challengeutils.wiki.validate_config("./")
            patch_read.assert_called_once_with("./")
            assert config == self.wiki_config

    def test_pull_wiki(self):
        """Testing pulling of wiki"""
        wiki_headers = [
            {
                "id": "2",
                "title": "Echoes",
                "parentId": "1"
            }
        ]
        expected_header = [
            {
                "id": "2",
                "title": "Echoes",
                "parentId": "1",
                "markdown_path": "Echoes.md"
            }
        ]
        wiki = synapseclient.Wiki(title="Echoes", owner="syn22",
                                  markdown="test")
        with patch.object(self.syn, "getWikiHeaders",
                          return_value=wiki_headers) as patch_get_headers,\
             patch.object(self.syn, "getWiki",
                          return_value=wiki) as patch_get_wiki:
            header = challengeutils.wiki.pull_wiki(
                self.syn, "syn1234", workdir=tempfile.gettempdir()
            )
            assert header == expected_header
            patch_get_headers.assert_called_once_with("syn1234")
            patch_get_wiki.assert_called_once_with("syn1234", subpageId="2")


    def test_push_wiki(self):
        """Testing push wiki"""
        wiki_obj = synapseclient.Wiki(title="Echoes", owner="syn22",
                                      markdown="test", id="44")
        self.wiki_config.append(
            {
                'title': 'Time',
                'parentId': '1',
                'markdown_path': self.file2.name
            }
        )

        expected_header = [
            {
                'id': '44',
                'title': 'Wish You Were Here',
                'markdown_path': self.file1.name
            },
            {
                'id': '2',
                'title': 'Echoes',
                'parentId': '1',
                'markdown_path': self.file2.name
            },
            {
                'title': 'Time',
                'parentId': '1',
                'markdown_path': self.file2.name,
                'id': '44'
            }
        ]
        with patch.object(challengeutils.wiki, "read_wiki_config",
                          return_value=self.wiki_config) as patch_read,\
             patch.object(self.syn, "store",
                          return_value=wiki_obj) as patch_store:
            header = challengeutils.wiki.push_wiki(
                self.syn, "syn1234", workdir=tempfile.gettempdir()
            )
            assert header == expected_header
            patch_read.assert_called_once_with(tempfile.gettempdir())
            assert patch_store.call_count == 2
