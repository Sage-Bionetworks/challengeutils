from mock import patch, call
import pytest
import challengeutils
import synapseclient

def setup_function(function):
    print('\nsetup_function()')


def test_wrong_permission_level():
    with pytest.raises(ValueError, match=r'permission_level must be one of these:.*'):
        challengeutils.permissions.set_entity_permissions("syn", "entity", principalid=None, permission_level="foo")


@pytest.fixture( params=[
    # tuple with (input, expectedOutput)
    ("syn", None, None, "view"),
    ("syn", None, None, "download"),
    ("syn", None, None, "edit"),
    ("syn", None, None, "edit_and_delete"),
    ("syn", None, None, "admin"),
    ("syn", None, None, "delete"),
    ])
def test_data(request):
    return request.param

def test_none_principalid(test_data):
    (syn, entity, principalid, permission_level) = test_data
    with pytest.raises(ValueError, match='principalid must not be None'):
        challengeutils.permissions.set_entity_permissions(syn, entity, principalid=principalid, permission_level=permission_level)


def test_set_permissions():
    syn = synapseclient.Synapse()
    permissions = {"set"}
    with patch.object(syn, "setPermissions", return_value=permissions) as patch_syn_set_permission:
        challengeutils.permissions.set_entity_permissions(syn, "syn12345", principalid="12345", permission_level="view")
        patch_syn_set_permission.assert_called_once_with("syn12345",accessType=['READ'],principalId='12345')


