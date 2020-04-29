import logging
import re
from typing import Union

from synapseclient import File, Folder, Project
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
SynapseWikiCls = Union[File, Folder, Project]


def replace_wiki_text(markdown: str, wiki_mapping: dict,
                      entity: SynapseWikiCls, dest: SynapseWikiCls) -> str:
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
        map_to_text = f"{dest.id}/wiki/{dest_subwiki}"
        markdown = re.sub(orig_text, map_to_text, markdown)
        # Some widgets that you fill in with synapse links
        # are auto encoded. / -> %2F
        orig_text = f"{entity.id}%2Fwiki%2F{entity_page_id}"
        map_to_text = f"{dest.id}%2Fwiki%2F{dest_subwiki}"
        markdown = re.sub(orig_text, map_to_text, markdown)
    markdown = re.sub(entity.id, dest.id, markdown)
    return markdown


def copy_attachments(syn, entity_wiki):
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


def _get_headers():
    pass

def mirrorwiki(syn, entity, destination, force_merge=False):
    """
    This script is responsible for mirroring wiki pages
    It relies on the wiki titles between two Synapse Projects to be
    The same and will merge the updates from entity's wikis to
    destination's wikis

    Args:
        entity: Synapse File, Project, Folder Entity or Id with
                Wiki you want to copy
        destination: Synapse File, Project, Folder Entity or Id
                     with Wiki that matches entity
        force_merge: this will update a page even if its the same

    Returns:
        nothing
    """
    entity = syn.get(entity, downloadFile=False)
    destination = syn.get(destination, downloadFile=False)
    # TODO: getWikiHeaders fails when there is no wiki
    entity_wiki = syn.getWikiHeaders(entity)
    try:
        destination_wiki = syn.getWikiHeaders(destination)
    except SynapseHTTPError:
        raise ValueError("The destination Project has no Wiki. Mirroring a"
                         " Wiki requires that the source and destination "
                         "Projects have the same structure. You may want "
                         "to use the copy wiki functionality provided "
                         "by 'synapseutils.copyWiki'")

    # Get mapping of wiki pages
    entity_wiki_pages = {}
    for wiki in entity_wiki:
        entity_wiki_pages[wiki['title']] = wiki['id']
    destination_wiki_pages = {}
    # Mapping dictionary containing wiki page mapping between
    # entity and destination
    wiki_mapping = {}
    for wiki in destination_wiki:
        destination_wiki_pages[wiki['title']] = wiki['id']
        # Account for pages that exist in the new page that
        # don't exist in the old page
        if entity_wiki_pages.get(wiki['title']) is not None:
            wiki_mapping[entity_wiki_pages[wiki['title']]] = wiki['id']
    # TODO: Need to account for new pages
    for title in entity_wiki_pages:
        entity_wiki = syn.getWiki(entity, entity_wiki_pages[title])
        # If destination wiki does not have the title page, do not update
        if destination_wiki_pages.get(title) is not None:
            destination_wiki = syn.getWiki(destination,
                                           destination_wiki_pages[title])
            if destination_wiki.markdown == entity_wiki.markdown and not force_merge:
                logger.info("Skipping page update: {}".format(title))
            else:
                logger.info("Updating: {}".format(title))
                markdown = replace_wiki_text(markdown=entity_wiki.markdown,
                                             wiki_mapping=wiki_mapping,
                                             entity=entity,
                                             dest=destination)
                destination_wiki.markdown = markdown

                new_attachments = copy_attachments(syn, entity_wiki)

                destination_wiki.update(
                    {'attachmentFileHandleIds': new_attachments}
                )
            destination_wiki = syn.store(destination_wiki)
        else:
            logger.info("{}: title not existent in destination wikis".format(title))
