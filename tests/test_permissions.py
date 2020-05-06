"""Test permissions"""
from unittest.mock import patch, create_autospec

import pytest
import synapseclient

from challengeutils import permissions

SYN = create_autospec(synapseclient.Synapse)
SET_PERMS = {"set"}


@pytest.mark.parametrize("entity,principalid,permission_level,mapped", [
    # tuple with (input, expectedOutput)
    (synapseclient.Project(), None, "view",
     permissions.ENTITY_PERMS_MAPPINGS['view']),
    (synapseclient.Folder(parentId="syn123"), None, "download",
     permissions.ENTITY_PERMS_MAPPINGS['download']),
    (synapseclient.Entity(), None, "edit",
     permissions.ENTITY_PERMS_MAPPINGS['edit']),
    (synapseclient.Schema(parentId="syn123"), None, "edit_and_delete",
     permissions.ENTITY_PERMS_MAPPINGS['edit_and_delete']),
    (synapseclient.File(parentId="syn123"), None, "admin",
     permissions.ENTITY_PERMS_MAPPINGS['admin']),
    (synapseclient.Entity(), None, "remove",
     permissions.ENTITY_PERMS_MAPPINGS['remove']),
    (synapseclient.Evaluation(contentSource="syn123"), None, "view",
     permissions.EVALUATION_PERMS_MAPPINGS['view']),
    (synapseclient.Evaluation(contentSource="syn123"), None, "submit",
     permissions.EVALUATION_PERMS_MAPPINGS['submit']),
    (synapseclient.Evaluation(contentSource="syn123"), None, "score",
     permissions.EVALUATION_PERMS_MAPPINGS['score']),
    (synapseclient.Evaluation(contentSource="syn123"), None, "admin",
     permissions.EVALUATION_PERMS_MAPPINGS['admin']),
    (synapseclient.Evaluation(contentSource="syn123"), None, "remove",
     permissions.EVALUATION_PERMS_MAPPINGS['remove'])])
def test__set_permissions(entity, principalid, permission_level, mapped):
    """Test mapping of ACL"""
    #(entity, principalid, permission_level, mapped) = test_data
    with patch.object(SYN, "setPermissions",
                      return_value=SET_PERMS) as patch_set_permission:
        permissions._set_permissions(SYN, entity, principalid=principalid,
                                     permission_level=permission_level)
        patch_set_permission.assert_called_once_with(entity,
                                                     principalId=principalid,
                                                     accessType=mapped)


def test_wrong_permission_level():
    """Error raised if incorrect permission level is passed in"""
    with pytest.raises(ValueError,
                       match=r'permission_level must be one of these:.*'):
        permissions._set_permissions(SYN, synapseclient.Entity(),
                                     principalid="3",
                                     permission_level="foo")


@pytest.mark.parametrize("entity", ["syn123",
                                    synapseclient.Entity(id="syn123")])
def test_get_user_entity_permissions(entity):
    """Tests getting user entity permissions"""
    with patch.object(SYN, "restGET") as patch_rest_get:
        permissions.get_user_entity_permissions(SYN, entity)
        patch_rest_get.assert_called_once_with("/entity/syn123/permissions")
