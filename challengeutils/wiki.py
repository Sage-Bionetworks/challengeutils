"""Download and sync wiki tools"""
import json
import os
import typing

import synapseclient
from synapseclient import Synapse


def pull_wiki(syn: Synapse, project: str,
              workdir: str = "./") -> typing.List[dict]:
    """Downloads each wikipage's content into a markdown file and
    stores a configuration file

    Args:
        syn: Synapse connection
        project: synapseclient.Project or its id
        workdir: Location to download markdown files and wiki_config.json
                 into. Defaults to location of where code is being
                 executed.

    Returns:
        Wiki Configuration
        [
            {
                "id": "111",
                "title": "title",
                "parentId": "33333",
                "markdown_path": "markdown.md"
            },
            {...}
        ]

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
            title = '_homepage_'
        markdown_path = os.path.join(workdir, f"{title}.md")
        with open(markdown_path, 'w') as md_file:
            md_file.write(wiki['markdown'])
        wiki_header['markdown_path'] = f"{title}.md"
    return wiki_headers


def read_wiki_config(workdir: str) -> typing.List[dict]:
    """Read wiki config file from working directory

    Args:
        workdir: Working directory

    Returns:
        Wiki Configuration
        [
            {
                "id": "111",
                "title": "title",
                "parentId": "33333",
                "markdown_path": "markdown.md"
            },
            {...}
        ]
    """
    config_path = os.path.join(workdir, "wiki_config.json")
    if not os.path.exists(config_path):
        raise ValueError("wiki_config.json must exist at specified workdir")
    with open(config_path, "r") as config:
        wiki_config = json.load(config)
    return wiki_config


def validate_config(workdir: str) -> typing.List[dict]:
    """Validates wiki configuration

    Args:
        workdir: Workfing directory with markdown and wiki_config.json

    Returns:
        Wiki Configuration
        [
            {
                "id": "111",
                "title": "title",
                "parentId": "33333",
                "markdown_path": "markdown.md"
            },
            {...}
        ]

    Raises:
        ValueError:
            `markdown_path` is specified but cannot be located.
            There are duplicated wiki ids.
            `id` is not specified and (`markdown_path`/`parentId`/`title`
            is missing or `parentId` not one of the `id`s.)
            `id` cannot be the same as `parentId`.

    """
    wiki_config = read_wiki_config(workdir)
    ids = [wiki_header['id'] for wiki_header in wiki_config
           if wiki_header.get('id') is not None]
    if len(set(ids)) != len(ids):
        raise ValueError("Must have unique ids.")
    for wiki_header in wiki_config:
        markdown_path = wiki_header.get('markdown_path')
        wikiid = wiki_header.get('id')
        parentid = wiki_header.get('parentId')
        title = wiki_header.get('title', '')
        # Markdown file must exist if specified
        if markdown_path is not None and not os.path.exists(
                os.path.join(workdir, markdown_path)):
            raise ValueError(f"{markdown_path} does not exist")
        # id must not be the same as parentid
        if wikiid == parentid:
            raise ValueError("`id` cannot be the same as `parentId`.")
        if (wikiid is None and
            (markdown_path is None or parentid not in ids
             or title == '')):
            raise ValueError("If `id` is not specified, then `markdown_path` "
                             "and `parentId`, and `title` must be specified. "
                             "`title` must also not be blank."
                             "`parentId` must be one of the "
                             "`id`s in the config.")
    return wiki_config


def push_wiki(syn: Synapse, projectid: str,
              workdir: str = "./") -> typing.List[dict]:
    """Syncs Wiki from configuration

    Args:
        syn: Synapse connection
        project: synapseclient.Project or its id
        workdir: Location to download markdown files and wiki_config.json.
                 Defaults to location of where code is being
                 executed.

    Returns:
        Wiki Configuration
        [
            {
                "id": "111",
                "title": "title",
                "parentId": "33333",
                "markdown_path": "markdown.md"
            },
            {...}
        ]

    """
    wiki_config = validate_config(workdir)
    for wiki_header in wiki_config:
        # no markdown path, nothing to update
        markdown_path = wiki_header.get('markdown_path')
        if not wiki_header.get('markdown_path'):
            print(f"Markdown not specified: {wiki_header['title']}")
            continue
        markdown_path = os.path.join(workdir, markdown_path)
        with open(markdown_path, 'r') as md_f:
            markdown = md_f.read()
        # Create new wiki page if id isn't specified
        if wiki_header.get('id') is not None:
            wiki = syn.getWiki(projectid, subpageId=wiki_header['id'])
            # Don't store if the wiki pages are the same
            if wiki.markdown == markdown:
                print(f"no updates: {wiki_header['title']}")
                continue
            print(f"Wiki updated: {wiki_header['title']}")
        else:
            wiki = synapseclient.Wiki(owner=projectid,
                                      title=wiki_header['title'],
                                      parentWikiId=wiki_header['parentId'])
            print(f"Wiki added: {wiki_header['title']}")
        wiki.markdown = markdown
        wiki = syn.store(wiki)
        # If new wiki page is added, must add to wiki_config.json
        wiki_header['id'] = wiki['id']
    return wiki_config
