import logging
import re
from typing import Union, List

from synapseclient import File, Folder, Project, Wiki, Synapse
try:
    from synapseclient.core.exceptions import SynapseHTTPError
except ModuleNotFoundError:
    # For synapseclient < v2.0
    from synapseclient.exceptions import SynapseHTTPError
import synapseutils

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PREVIEW_FILE_HANDLE = "org.sagebionetworks.repo.model.file.PreviewFileHandle"
# These are the synapse entities that can have wikis
SynapseWikiCls = Union[File, Folder, Project]


def replace_wiki_text(markdown: str, wiki_mapping: dict,
                      entity: SynapseWikiCls,
                      destination: SynapseWikiCls) -> str:
    """Remap wiki text with correct synapse links

    Args:
        markdown: Markdown text
        wiki_mapping: mapping of old to new wiki pages
        entity: Synapse entity with wiki
        dest: Synapse entity with wiki

    Returns:
        Remapped markdown string

    """
    for entity_page_id in wiki_mapping:
        dest_subwiki = wiki_mapping[entity_page_id]
        # Replace the wiki
        orig_text = f"{entity.id}/wiki/{entity_page_id}"
        map_to_text = f"{destination.id}/wiki/{dest_subwiki}"
        markdown = re.sub(orig_text, map_to_text, markdown)
        # Some widgets that you fill in with synapse links
        # are auto encoded. / -> %2F
        orig_text = f"{entity.id}%2Fwiki%2F{entity_page_id}"
        map_to_text = f"{destination.id}%2Fwiki%2F{dest_subwiki}"
        markdown = re.sub(orig_text, map_to_text, markdown)
    markdown = re.sub(entity.id, destination.id, markdown)
    return markdown


def copy_attachments(syn: Synapse, entity_wiki: Wiki):
    """Copy wiki attachments

    Args:
        syn: Synapse connection
        entity_wiki: Wiki you are copying

    """
    # All attachments must be updated
    if entity_wiki['attachmentFileHandleIds']:
        attachments = [
            syn._getFileHandleDownload(filehandleid,
                                       entity_wiki.id,
                                       objectType='WikiAttachment')
            for filehandleid in entity_wiki['attachmentFileHandleIds']
        ]
        # Remove preview attachments
        no_previews = [
            attachment['fileHandle'] for attachment in attachments
            if attachment['fileHandle']['concreteType'] != PREVIEW_FILE_HANDLE
        ]
        content_types = [attachment['contentType']
                         for attachment in no_previews]
        file_names = [attachment['fileName'] for attachment in no_previews]
        copied_filehandles = synapseutils.copyFileHandles(
            syn, no_previews, ["WikiAttachment"]*len(no_previews),
            [entity_wiki.id]*len(no_previews),
            content_types, file_names
        )
        new_attachments = [filehandle['newFileHandle']['id']
                           for filehandle in copied_filehandles]
    else:
        new_attachments = []
    return new_attachments


def _get_headers(syn: Synapse, entity: SynapseWikiCls) -> List[dict]:
    """Get wiki headers.

    Args:
        syn: Synapse connection
        entity: A Synapse Entity

    Returns:
        List of wiki headers
    """

    try:
        wiki_headers = syn.getWikiHeaders(entity)
    except SynapseHTTPError:
        raise ValueError(f"{entity.name} has no Wiki. Mirroring wikis "
                         "require that both `entity` and `destination` "
                         "have the same wiki structure. If you want to copy "
                         "a wiki page from `entity` to `destination`, you may "
                         "want to use `synapseutils.copyWiki`")
    return wiki_headers


def update_wiki(syn, entity_wiki_pages, destination_wiki_pages,
                force=False, dryrun=False, **kwargs):
    """Updates wiki pages.

    Args:
        entity_wiki_pages: Mapping between wiki title and synapseclient.Wiki
        destination_wiki_pages: Mapping between wiki title and
                                synapseclient.Wiki
        force: This will update a page even if its the same. Default is False.

        **kwargs: Same parameters as mirrorwiki.replace_wiki_text

    """
    for title in entity_wiki_pages:
        # If destination wiki does not have the title page, do not update
        if destination_wiki_pages.get(title) is None:
            logger.info(f"Title doesn't exist at destination: {title}")
            continue

        # Generate new markdown text
        entity_wiki = entity_wiki_pages[title]
        destination_wiki = destination_wiki_pages[title]
        markdown = replace_wiki_text(markdown=entity_wiki.markdown,
                                     **kwargs)

        if destination_wiki.markdown == markdown and not force:
            logger.info(f"No page updates: {title}")
        else:
            logger.info(f"Updating: {title}")
            destination_wiki.markdown = markdown

        # Should copy over the attachments every time because
        # someone could name attachments with the same name
        new_attachments = copy_attachments(syn, entity_wiki)

        destination_wiki.update(
            {'attachmentFileHandleIds': new_attachments}
        )
        if not dryrun:
            destination_wiki = syn.store(destination_wiki)


def _get_wikipages_and_mapping(syn: Synapse, entity: SynapseWikiCls,
                               destination: SynapseWikiCls) -> dict:
    """Get entity/destination pages and mapping of wiki pages

    Args:
        syn: Synapse connection
        entity: Synapse File, Project, Folder Entity or Id with
                Wiki you want to copy
        destination: Synapse File, Project, Folder Entity or Id
                     with Wiki that matches entity

    Returns:
        {'entity_wiki_pages': {'title': synapseclient.Wiki}
         'destination_wiki_pages': {'title': synapseclient.Wiki}
         'wiki_mapping': {'wiki_id': 'dest_wiki_id'}}

    """
    entity_wiki = _get_headers(syn, entity)
    destination_wiki = _get_headers(syn, destination)

    entity_wiki_pages = {}
    for wiki in entity_wiki:
        entity_wiki = syn.getWiki(entity, wiki['id'])
        entity_wiki_pages[wiki['title']] = entity_wiki

    # Mapping dictionary containing wiki page mapping between
    # entity and destination
    wiki_mapping = {}
    destination_wiki_pages = {}
    for wiki in destination_wiki:
        destination_wiki = syn.getWiki(destination, wiki['id'])
        destination_wiki_pages[wiki['title']] = destination_wiki
        # Account for pages that exist in the new page that
        # don't exist in the old page
        if entity_wiki_pages.get(wiki['title']) is not None:
            wiki_mapping[entity_wiki_pages[wiki['title']].id] = wiki['id']
    return {'entity_wiki_pages': entity_wiki_pages,
            'destination_wiki_pages': destination_wiki_pages,
            'wiki_mapping': wiki_mapping}


def mirror(syn: Synapse, entity: SynapseWikiCls,
           destination: SynapseWikiCls, force=False,
           dryrun=False):
    """Mirrors (sync) wiki pages by using the wikipage titles between two
    Synapse Entities.  This function only works if `entity` and `destination`
    are the same type and both must have wiki pages.  Only wiki pages with the
    same titles will be copied from `entity` to `destination` - if there is
    a wiki page that you want to add, you will have to create a wiki page
    first in the `destination` with the same name.

    Args:
        entity: Synapse File, Project, Folder Entity or Id with
                Wiki you want to copy
        destination: Synapse File, Project, Folder Entity or Id
                     with Wiki that matches entity
        force: Update a page even if its the same. Default to False.
        dryrun: Show the pages that have changed but don't update. Default
                is False.

    """
    entity = syn.get(entity, downloadFile=False)
    destination = syn.get(destination, downloadFile=False)
    if type(entity) is not type(destination):
        raise ValueError("Can only mirror wiki pages between similar "
                         "entity types")

    # Get entity/destination pages and mapping of wiki pages
    pages_and_mappings = _get_wikipages_and_mapping(syn, entity,
                                                    destination)

    if dryrun:
        logger.info("Your wiki pages will not be mirrored. `dryrun` is True")
    update_wiki(syn, **pages_and_mappings,
                force=force, dryrun=dryrun,
                entity=entity,
                destination=destination)
