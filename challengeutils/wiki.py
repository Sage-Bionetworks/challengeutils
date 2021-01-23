"""Download and sync wiki tools"""
import json
import os

import synapseclient
from synapseclient import Synapse


def download_wiki(syn: Synapse, project: str,
                  markdown_location: str = "./",
                  config_path: str = "wiki_config.json") -> dict:
    """Downloads each wikipage's content into a markdown file and
    stores a configuration file

    Args:
        syn: Synapse connection
        project: synapseclient.Project or its id
        markdown_location: Location to download markdown files into
                           Defaults to location of where code is being
                           executed.
        config_path: Wiki configuration path that can be used to update
                     the wikis

    Returns:
        Dict of wiki configuration

    """
    projectid = synapseclient.core.utils.id_of(project)
    wiki_headers = syn.getWikiHeaders(projectid)
    for wiki_header in wiki_headers:
        wiki = syn.getWiki(projectid, subpageId=wiki_header['id'])
        # Convert all special characters to underscore
        title = ''.join(letter for letter in wiki['title']
                        if letter.isalnum())
        # Home page title is always blank
        if title == '':
            title = 'home'
        markdown_path = os.path.join(markdown_location,
                                     f"{title}.md")
        with open(markdown_path, 'w') as md_file:
            md_file.write(wiki['markdown'])
        wiki_header['markdown_path'] = os.path.abspath(markdown_path)
    with open(config_path, 'w') as config:
        json.dump(wiki_headers, config, indent=4)
    return wiki_headers


def _validate_config(wiki_config: dict):
    """Validates wiki configuration

    Args:
        wiki_config: Wiki configuration dict

    Raises:
        ValueError:
            `markdown_path` is specified but cannot be located
            There are more than one `title` that is ''
            `id` is not specified and `markdown_path`/`parentId`/`title`
            is missing or `parentId` not one of the `id`s.

    """
    ids = [wiki_header['id'] for wiki_header in wiki_config
           if wiki_header.get('id') is not None]
    home_page_count = 0
    for wiki_header in wiki_config:
        markdown_path = wiki_header.get('markdown_path')
        wikiid = wiki_header.get('id')
        parentid = wiki_header.get('parentId')
        title = wiki_header.get('title')
        # Markdown file must exist if specified
        if markdown_path is not None and not os.path.exists(markdown_path):
            raise ValueError(f"{markdown_path} does not exist")
        # Cannot have more than one page without a title (Only the home page)
        # Can have no title
        if title == '':
            home_page_count += 1
        if home_page_count > 1:
            raise ValueError("Cannot have more than one page without a "
                             "`title`")
        if (wikiid is None and
            (markdown_path is None or parentid not in ids
             or title is None)):
            raise ValueError("If `id` is not specified, then `markdown_path` "
                             "and `parentId`, and `title` must be specified. "
                             "`parentId` must be one of the "
                             "`id`s in the config.")


def validate_config(config_path: str):
    """Validates wiki configuration

    Args:
        config_path: Wiki configuration path

    Raises:
        ValueError:
            `markdown_path` is specified but cannot be located
            There are more than one `title` that is ''
            `id` is not specified and `markdown_path`/`parentId`/`title`
            is missing or `parentId` not one of the `id`s.

    """
    with open(config_path, "r") as config:
        wiki_config = json.load(config)
    _validate_config(wiki_config)


def sync_wiki(syn: Synapse, projectid: str, config_path: str) -> dict:
    """Syncs Wiki from configuration

    Args:
        syn: Synapse connection
        project: synapseclient.Project or its id
        config_path: Wiki configuration path that can be used to update
                     the wikis

    Returns:
        Dict of wiki configuration

    """
    with open(config_path, "r") as config:
        wiki_config = json.load(config)

    _validate_config(wiki_config)

    for wiki_header in wiki_config:
        # no markdown path, nothing to update
        if not wiki_header.get('markdown_path'):
            print(f"Markdown not specified: {wiki_header['title']}")
            continue
        with open(wiki_header['markdown_path'], 'r') as md_f:
            markdown = md_f.read()
        if wiki_header.get('id') is not None:
            wiki = syn.getWiki(projectid, subpageId=wiki_header['id'])
            # Don't store if the wiki pages are the same
            if wiki.markdown == markdown:
                print(f"no updates: {wiki_header['title']}")
                continue
        else:
            wiki = synapseclient.Wiki(owner=projectid,
                                      title=wiki_header['title'],
                                      parentWikiId=wiki_header['parentId'])
        print(f"Wiki added/updated: {wiki_header['title']}")
        wiki.markdown = markdown
        syn.store(wiki)

    return wiki_config
