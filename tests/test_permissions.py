from mock import patch
import pytest
import challengeutils
import synapseclient
syn = synapseclient.Synapse()
SET_PERMS = {"set"}


@pytest.fixture(params=[
    # tuple with (input, expectedOutput)
    (synapseclient.Project(), None, "view",
        challengeutils.permissions.ENTITY_PERMS_MAPPINGS['view']),
    (synapseclient.Folder(parentId="syn123"), None, "download",
        challengeutils.permissions.ENTITY_PERMS_MAPPINGS['download']),
    (synapseclient.Entity(), None, "edit",
        challengeutils.permissions.ENTITY_PERMS_MAPPINGS['edit']),
    (synapseclient.Schema(parentId="syn123"), None, "edit_and_delete",
        challengeutils.permissions.ENTITY_PERMS_MAPPINGS['edit_and_delete']),
    (synapseclient.File(parentId="syn123"), None, "admin",
        challengeutils.permissions.ENTITY_PERMS_MAPPINGS['admin']),
    (synapseclient.Entity(), None, "remove",
        challengeutils.permissions.ENTITY_PERMS_MAPPINGS['remove']),
    (synapseclient.Evaluation(contentSource="syn123"), None, "view",
        challengeutils.permissions.EVALUATION_PERMS_MAPPINGS['view']),
    (synapseclient.Evaluation(contentSource="syn123"), None, "submit",
        challengeutils.permissions.EVALUATION_PERMS_MAPPINGS['submit']),
    (synapseclient.Evaluation(contentSource="syn123"), None, "score",
        challengeutils.permissions.EVALUATION_PERMS_MAPPINGS['score']),
    (synapseclient.Evaluation(contentSource="syn123"), None, "admin",
        challengeutils.permissions.EVALUATION_PERMS_MAPPINGS['admin']),
    (synapseclient.Evaluation(contentSource="syn123"), None, "remove",
        challengeutils.permissions.EVALUATION_PERMS_MAPPINGS['remove']),
    ])
def test_data(request):
    return request.param


def test__set_permissions(test_data):
    (entity, principalid, permission_level, mapped) = test_data
    with patch.object(syn, "setPermissions",
                      return_value=SET_PERMS) as patch_syn_set_permission:
        challengeutils.permissions._set_permissions(
            syn, entity, principalid=principalid,
            permission_level=permission_level)
        patch_syn_set_permission.assert_called_once_with(
            entity,
            principalId=principalid,
            accessType=mapped)


def test_wrong_permission_level():
    with pytest.raises(ValueError,
                       match=r'permission_level must be one of these:.*'):
        challengeutils.permissions._set_permissions(
            syn, synapseclient.Entity(), principalid="3",
            permission_level="foo")
