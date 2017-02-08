import synapseclient
from synapseclient import File, Project, Folder, Table, Schema, Link, Wiki, Activity, exceptions
from synapseclient.exceptions import *
import tempfile
import re

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
                print("Skipping page update %s", title)
            else:
                newWiki.markdown = oldWiki.markdown
                for oldId in mapping:
                    oldProjectAndWikiId = "%s/wiki/%s" % (entity, oldId)
                    newProjectAndWikiId = "%s/wiki/%s" % (destinationId, mapping[oldId])
                    newWiki.markdown=re.sub(oldProjectAndWikiId, newProjectAndWikiId, newWiki.markdown)
                newWiki.markdown=re.sub(entity, destinationId, newWiki.markdown)
            print("Updating attachments")
            if oldWiki['attachmentFileHandleIds'] == []:
                attachments = []
            elif oldWiki['attachmentFileHandleIds'] != []:
                uri = "/entity/%s/wiki/%s/attachmenthandles" % (oldWiki.ownerId, oldWiki.id)
                results = syn.restGET(uri)
                file_handles = {fh['id']:fh for fh in results['list']}
                # TODO: CHeck md5 so no need to upload everytime?
                attachments = []
                tempdir = tempfile.gettempdir()
                for fhid in oldWiki.attachmentFileHandleIds:
                    file_info = syn._downloadWikiAttachment(oldWiki.ownerId, oldWiki, file_handles[fhid]['fileName'], destination=tempdir)
                    attachments.append(file_info['path'])
            newWiki.update({'attachments':attachments})
            newWiki = syn.store(newWiki)
        else:
            print("%s: title not existent in destination wikis" % title)


syn = synapseclient.login()
mergeWiki(syn, "syn4219927", "syn4224222")