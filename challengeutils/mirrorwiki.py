import synapseclient
import synapseutils as synu
import re

def mirrorwiki(syn, entity, destination, force_merge=False):
    """
    This script is responsible for mirroring wiki pages
    It relies on the wiki titles between two Synapse Projects to be 
    The same and will merge the updates from entity's wikis to destination's wikis

    Args:
        entity: Synapse File, Project, Folder Entity or Id with Wiki you want to copy
        destination: Synapse File, Project, Folder Entity or Id with Wiki that matches entity
        force_merge: this will update a page even if its the same
    
    Returns:
        nothing
    """
    entity = syn.get(entity,downloadFile=False)
    destination = syn.get(destination, downloadFile=False)
    # TODO: getWikiHeaders fails when there is no wiki
    entity_wiki = syn.getWikiHeaders(entity)
    try:
        destination_wiki = syn.getWikiHeaders(destination)
    except synapseclient.exceptions.SynapseHTTPError  as e:
        raise ValueError("The destination Project has no Wiki. Mirroring a Wiki requires that the source and destination Projects have the same structure. You may want to use the copy wiki functionality provided by 'synapseutils.copyWiki'")

    #Get mapping of wiki pages
    entity_wiki_pages = {}
    for wiki in entity_wiki:
        entity_wiki_pages[wiki['title']] = wiki['id']
    destination_wiki_pages = {}
    #Mapping dictionary containing wiki page mapping between entity and destination
    wiki_mapping = {}
    for wiki in destination_wiki:
        destination_wiki_pages[wiki['title']] = wiki['id']
        #Account for pages that exist in the new page that don't exist in the old page
        if entity_wiki_pages.get(wiki['title']) is not None:
            wiki_mapping[entity_wiki_pages[wiki['title']]] = wiki['id']
    ### TODO: Need to account for new pages ###
    for title in entity_wiki_pages:
        entity_wiki = syn.getWiki(entity, entity_wiki_pages[title])
        #If destination wiki does not have the title page, do not update
        if destination_wiki_pages.get(title) is not None:
            destination_wiki = syn.getWiki(destination, destination_wiki_pages[title])
            if destination_wiki.markdown == entity_wiki.markdown and not force_merge:
                print("Skipping page update: %s" % title)
            else:
                print("Updating: %s" % title)
                destination_wiki.markdown = entity_wiki.markdown
                for entity_page_id in wiki_mapping:
                    entity_project_and_wiki_id = "%s/wiki/%s" % (entity.id, entity_page_id)
                    destination_project_and_wiki_id = "%s/wiki/%s" % (destination.id, wiki_mapping[entity_page_id])
                    destination_wiki.markdown=re.sub(entity_project_and_wiki_id, destination_project_and_wiki_id, destination_wiki.markdown)
                destination_wiki.markdown=re.sub(entity.id, destination.id, destination_wiki.markdown)
            #All attachments must be updated
            if entity_wiki['attachmentFileHandleIds'] == []:
                new_file_handles = []
            elif entity_wiki['attachmentFileHandleIds'] != []:
                attachments = [syn._getFileHandleDownload(filehandleid, entity_wiki.id, objectType='WikiAttachment') for filehandleid in entity_wiki['attachmentFileHandleIds']]
                #Remove preview attachments
                no_previews = [attachment['fileHandle'] for attachment in attachments if attachment['fileHandle']['concreteType'] != "org.sagebionetworks.repo.model.file.PreviewFileHandle"]
                content_types = [attachment['contentType'] for attachment in no_previews]
                file_names = [attachment['fileName'] for attachment in no_previews]
                copied_filehandles = synu.copyFileHandles(syn, no_previews, ["WikiAttachment"]*len(no_previews), [entity_wiki.id]*len(no_previews), content_types, file_names)
                new_attachments = [filehandle['newFileHandle']['id'] for filehandle in copied_filehandles['copyResults']]
            destination_wiki.update({'attachmentFileHandleIds':new_attachments})
            destination_wiki = syn.store(destination_wiki)
        else:
            print("%s: title not existent in destination wikis" % title)
