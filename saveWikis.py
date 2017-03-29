import synapseclient
from synapseclient import File, Project, Folder, Table, Schema, Link, Wiki, Entity, Activity, exceptions
import time
from synapseclient.exceptions import *
import tempfile
import re
import json
def _getSubWikiHeaders(wikiHeaders,subPageId,mapping=None):
    """
    Function to assist in getting wiki headers of subwikipages
    """
    subPageId = str(subPageId)
    for i in wikiHeaders:
        # This is for the first match 
        # If it isnt the actual parent, it will turn the first match into a parent node which will not have a parentId
        if i['id'] == subPageId:
            if mapping is None:
                i.pop("parentId",None)
                mapping = [i]
            else:
                mapping.append(i)
        elif i.get('parentId') == subPageId:
            mapping = _getSubWikiHeaders(wikiHeaders,subPageId=i['id'],mapping=mapping)
    return(mapping)


def _updateSynIds(newWikis, wikiIdMap, entityMap):
    print("Updating Synapse references:\n")
    for oldWikiId in wikiIdMap.keys():
        # go through each wiki page once more:
        newWikiId = wikiIdMap[oldWikiId]
        newWiki = newWikis[newWikiId]
        print('Updated Synapse references for Page: %s\n' %newWikiId)
        s = newWiki.markdown

        for oldSynId in entityMap.keys():
            # go through each wiki page once more:
            newSynId = entityMap[oldSynId]
            oldSynId = oldSynId + "\\b"
            s = re.sub(oldSynId, newSynId, s)
        print("Done updating Synpase IDs.\n")
        newWikis[newWikiId].markdown = s
    return(newWikis)


def _updateInternalLinks(newWikis, wikiIdMap, entity, destinationId ):
    print("Updating internal links:\n")
    for oldWikiId in wikiIdMap.keys():
        # go through each wiki page once more:
        newWikiId=wikiIdMap[oldWikiId]
        newWiki=newWikis[newWikiId]
        print("\tUpdating internal links for Page: %s\n" % newWikiId)
        s=newWiki.markdown
        # in the markdown field, replace all occurrences of entity/wiki/abc with destinationId/wiki/xyz,
        # where wikiIdMap maps abc->xyz
        # replace <entity>/wiki/<oldWikiId> with <destinationId>/wiki/<newWikiId> 
        for oldWikiId2 in wikiIdMap.keys():
            oldProjectAndWikiId = "%s/wiki/%s\\b" % (entity, oldWikiId2)
            newProjectAndWikiId = "%s/wiki/%s" % (destinationId, wikiIdMap[oldWikiId2])
            s=re.sub(oldProjectAndWikiId, newProjectAndWikiId, s)
        # now replace any last references to entity with destinationId
        s=re.sub(entity, destinationId, s)
        newWikis[newWikiId].markdown=s
    return(newWikis)

def copyWiki(syn, entity, destinationId, entitySubPageId=None, destinationSubPageId=None, updateLinks=True, updateSynIds=True, entityMap=None):
    """
    Copies wikis and updates internal links
    :param syn:                     A synapse object: syn = synapseclient.login()- Must be logged into synapse
    :param entity:                  A synapse ID of an entity whose wiki you want to copy
    :param destinationId:           Synapse ID of a folder/project that the wiki wants to be copied to
    
    :param updateLinks:             Update all the internal links. (e.g. syn1234/wiki/34345 becomes syn3345/wiki/49508)
                                    Defaults to True
    :param updateSynIds:            Update all the synapse ID's referenced in the wikis. (e.g. syn1234 becomes syn2345)
                                    Defaults to True but needs an entityMap
    :param entityMap:               An entity map {'oldSynId','newSynId'} to update the synapse IDs referenced in the wiki
                                    Defaults to None 
    :param entitySubPageId:         Can specify subPageId and copy all of its subwikis
                                    Defaults to None, which copies the entire wiki
                                    subPageId can be found: https://www.synapse.org/#!Synapse:syn123/wiki/1234
                                    In this case, 1234 is the subPageId. 
    :param destinationSubPageId:    Can specify destination subPageId to copy wikis to
                                    Defaults to None
    :returns: A list of Objects with three fields: id, title and parentId.
    """
    stagingSyn = synapseclient.login()
    stagingSyn.setEndpoints(**synapseclient.client.STAGING_ENDPOINTS)
    oldOwn = stagingSyn.get(entity,downloadFile=False)
    # getWikiHeaders fails when there is no wiki
    try:
        oldWh = stagingSyn.getWikiHeaders(oldOwn)
    except SynapseHTTPError as e:
        if e.response.status_code == 404:
            return([])
        else:
            raise e

    if entitySubPageId is not None:
        oldWh = _getSubWikiHeaders(oldWh,entitySubPageId)
    newOwn =syn.get(destinationId,downloadFile=False)
    wikiIdMap = dict()
    newWikis = dict()
    for wikiHeader in oldWh:
        attDir=tempfile.NamedTemporaryFile(prefix='attdir',suffix='')
        #print i['id']
        wiki = stagingSyn.getWiki(oldOwn, wikiHeader.id)
        print('Got wiki %s' % wikiHeader.id)
        if wiki['attachmentFileHandleIds'] == []:
            attachments = []
        elif wiki['attachmentFileHandleIds'] != []:
            attachments = []
            tempdir = tempfile.gettempdir()
            for filehandleId in wiki['attachmentFileHandleIds']:
                result = stagingSyn._getFileHandleDownload(filehandleId, wiki.id, objectType='WikiAttachment')
                file_info = stagingSyn._downloadFileHandle(result['preSignedURL'],tempdir,result['fileHandle'])
                attachments.append(file_info)
        #for some reason some wikis don't have titles?
        if hasattr(wikiHeader, 'parentId'):
            wNew = Wiki(owner=newOwn, title=wiki.get('title',''), markdown=wiki.markdown, attachments=attachments, parentWikiId=wikiIdMap[wiki.parentWikiId])
            wNew = syn.store(wNew)
        else:
            if destinationSubPageId is not None:
                wNew = syn.getWiki(newOwn, destinationSubPageId)
                wNew.attachments = attachments
                wNew.markdown = wiki.markdown
                #Need to add logic to update titles here
                wNew = syn.store(wNew)
            else:
                wNew = Wiki(owner=newOwn, title=wiki.get('title',''), markdown=wiki.markdown, attachments=attachments, parentWikiId=destinationSubPageId)
                wNew = syn.store(wNew)
        newWikis[wNew.id]=wNew
        wikiIdMap[wiki.id] =wNew.id

    if updateLinks:
        newWikis = _updateInternalLinks(newWikis, wikiIdMap, entity, destinationId)

    if updateSynIds and entityMap is not None:
        newWikis = _updateSynIds(newWikis, wikiIdMap, entityMap)
    
    print("Storing new Wikis\n")
    for oldWikiId in wikiIdMap.keys():
        newWikiId = wikiIdMap[oldWikiId]
        newWikis[newWikiId] = syn.store(newWikis[newWikiId])
        print("\tStored: %s\n" % newWikiId)
    newWh = syn.getWikiHeaders(newOwn)
    return(newWh)