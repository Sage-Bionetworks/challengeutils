"""Pull and push wiki tools"""
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
        Wiki Configuration::

            [
                {
                    "id": "111",
                    "title": "homepage",
                    "markdown_path": "111-homepage.md"
                },
                {...}
            ]

    """
    projectid = synapseclient.core.utils.id_of(project)
    wiki_headers = syn.getWikiHeaders(projectid)
    for wiki_header in wiki_headers:
        wiki = syn.getWiki(projectid, subpageId=wiki_header['id'])
        # Convert all special characters to underscore
        # This way markdown paths don't have special characters
        # and json file can be written without encoding
        clean_title = ''.join(letter for letter in wiki['title']
                              if letter.isalnum())
        # Home page title is always blank
        if clean_title == '':
            clean_title = 'homepage'
            wiki_header['title'] = clean_title
        # The wiki id is added to the markdown path because wiki ids are
        # unique, but wiki titles don't have to be
        markdown_path = os.path.join(workdir, f"{wiki.id}-{clean_title}.md")
        with open(markdown_path, 'w') as md_file:
            md_file.write(wiki['markdown'])
        wiki_header['markdown_path'] = f"{wiki.id}-{clean_title}.md"
    return wiki_headers


def read_wiki_config(workdir: str) -> typing.List[dict]:
    """Read wiki config file from working directory

    Args:
        workdir: Working directory

    Returns:
        Wiki Configuration::

            [
                {
                    "id": "111",
                    "title": "title",
                    "parentId": "33333",
                    "markdown_path": "home.md"
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
        Wiki Configuration::

            [
                {
                    "id": "111",
                    "title": "title",
                    "parentId": "33333",
                    "markdown_path": "home.md"
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
    ids = [str(wiki_header['id']) for wiki_header in wiki_config
           if wiki_header.get('id') is not None]
    if len(set(ids)) != len(ids):
        raise ValueError("Must have unique ids.")

    # Must have one home page where `parentId` is blank
    home_page = [wiki_header.get('parentId') is None
                 for wiki_header in wiki_config]
    if sum(home_page) != 1:
        raise ValueError("Must only have one config "
                         "where `parentId` is blank")
    for wiki_header in wiki_config:
        # Configuration must not be empty
        markdown_path = wiki_header.get('markdown_path')
        wikiid = wiki_header.get('id')
        parentid = wiki_header.get('parentId')
        title = wiki_header.get('title')
        # Title must be specified
        if title is None:
            raise ValueError("Must have title")
        title = str(title).strip()

        # Make id and parentid strings and strip white spaces if values
        # are specified
        if wikiid is not None:
            wikiid = str(wikiid).strip()
            wiki_header['id'] = wikiid
        if parentid is not None:
            parentid = str(parentid).strip()
            wiki_header['parentId'] = parentid

        # id and parentid must not be empty strings
        if wikiid == '' or parentid == '' or title == '':
            raise ValueError('`id`, `parentId`, and `title` must not be '
                             'empty strings if specified')
        # Markdown file must exist if specified
        if markdown_path is not None and not os.path.isfile(
                os.path.join(workdir, markdown_path)):
            raise ValueError(f"{markdown_path} does not exist")
        # id must not be the same as parentid, but if both aren't specified,
        # This error shouldn't be raised
        if wikiid is not None and parentid is not None and wikiid == parentid:
            raise ValueError("`id` and `parentId` can't be equal.")
        # If parentid is specified, it has to be in one of the `ids`
        if parentid is not None and parentid not in ids:
            raise ValueError("`parentId` must be one of the "
                             "`id`s in the config")
    return wiki_config


def push_wiki(syn: Synapse, projectid: str,
              workdir: str = "./") -> typing.List[dict]:
    """Pushes Wiki from configuration

    Args:
        syn: Synapse connection
        project: synapseclient.Project or its id
        workdir: Location to download markdown files and wiki_config.json.
                 Defaults to location of where code is being
                 executed.

    Returns:
        Wiki Configuration::

            [
                {
                    "id": "111",
                    "title": "title",
                    "parentId": "33333",
                    "markdown_path": "home.md"
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
