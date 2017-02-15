import synapseclient
from synapseclient import File, Project, Folder, Table, Schema, Link, Wiki, Activity
from synapseclient.exceptions import *
import synapseutils as synu
import tempfile
import re
import argparse

def mergeWiki(syn, entity, destinationId, forceMerge=False):
    oldOwn = syn.get(entity,downloadFile=False)
    destinationOwn = syn.get(destinationId, downloadFile=False)
    # TODO: getWikiHeaders fails when there is no wiki
    oldWh = syn.getWikiHeaders(oldOwn)
    newWh = syn.getWikiHeaders(destinationOwn)
    #Get mapping of wiki pages
    old_child_pages = {}
    for c in oldWh:
        old_child_pages[c['title']] = c['id']
    new_child_pages = {}
    mapping = {}
    for c in newWh:
        new_child_pages[c['title']] = c['id']
        #Account for pages that exist in the new page that don't exist in the old page
        if old_child_pages.get(c['title']) is not None:
            mapping[old_child_pages[c['title']]] = c['id']
    ### TODO: Need to account for new pages ###
    for title in old_child_pages:
        oldWiki = syn.getWiki(entity, old_child_pages[title])
        #If destination wiki does not have the title page, do not update
        if new_child_pages.get(title) is not None:
            newWiki = syn.getWiki(destinationId, new_child_pages[title])
            if newWiki.markdown == oldWiki.markdown and not forceMerge:
                print("Skipping page update: %s" % title)
            else:
                print("Updating: %s" % title)
                newWiki.markdown = oldWiki.markdown
                for oldId in mapping:
                    oldProjectAndWikiId = "%s/wiki/%s" % (entity, oldId)
                    newProjectAndWikiId = "%s/wiki/%s" % (destinationId, mapping[oldId])
                    newWiki.markdown=re.sub(oldProjectAndWikiId, newProjectAndWikiId, newWiki.markdown)
                newWiki.markdown=re.sub(entity, destinationId, newWiki.markdown)
            #All attachments must be updated
            if oldWiki['attachmentFileHandleIds'] == []:
                new_file_handles = []
            elif oldWiki['attachmentFileHandleIds'] != []:
                results = [syn._getFileHandleDownload(filehandleId, oldWiki.id, objectType='WikiAttachment') for filehandleId in oldWiki['attachmentFileHandleIds']]
                nopreviews = [attach['fileHandle'] for attach in results if attach['fileHandle']['concreteType'] != "org.sagebionetworks.repo.model.file.PreviewFileHandle"]
                copiedFileHandles = synu.copyFileHandles(syn, nopreviews, ["WikiAttachment"]*len(nopreviews), [oldWiki.id]*len(nopreviews))
                new_file_handles = [filehandle['newFileHandle']['id'] for filehandle in copiedFileHandles['copyResults']]
            newWiki.update({'attachmentFileHandleIds':new_file_handles})
            newWiki = syn.store(newWiki)
        else:
            print("%s: title not existent in destination wikis" % title)

def command_mergeWiki(syn, args):
    mergeWiki(syn, args.id, args.destinationId, args.forceMerge)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Merge wiki')
    parser.add_argument("id", type=str,
                        help="Synapse ID of the project's wiki you want to copy")
    parser.add_argument("destinationId", type=str,
                        help='Synapse ID of project where wiki will be copied to')
    parser.add_argument("--forceMerge", action='store_true',
                        help='Force the merge of wiki markdowns')
    args = parser.parse_args()
    syn = synapseclient.login()
    command_mergeWiki(syn, args)