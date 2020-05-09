"""Convenience functions to set permissions on Synapse entities,
without having to know the granular access control list"""
import synapseclient
from synapseclient.core.utils import id_of

VIEW = ["READ"]
SUBMIT = ['READ', 'SUBMIT']
DOWNLOAD = ['READ', 'DOWNLOAD']
EDIT = ['DOWNLOAD', 'UPDATE', 'READ', 'CREATE']
EDIT_AND_DELETE = ['DOWNLOAD', 'UPDATE', 'READ', 'CREATE', 'DELETE']
SCORE = ['READ', 'UPDATE_SUBMISSION', 'READ_PRIVATE_SUBMISSION']
ADMIN_EVALS = ['DELETE_SUBMISSION', 'DELETE', 'SUBMIT', 'UPDATE',
               'CREATE', 'READ', 'UPDATE_SUBMISSION',
               'READ_PRIVATE_SUBMISSION', 'CHANGE_PERMISSIONS']
ADMIN = ['DELETE', 'CHANGE_SETTINGS', 'MODERATE', 'CREATE', 'READ',
         'DOWNLOAD', 'UPDATE', 'CHANGE_PERMISSIONS']
EVALUATION_PERMS_MAPPINGS = {'view': VIEW,
                             'submit': SUBMIT,
                             'score': SCORE,
                             'admin': ADMIN_EVALS,
                             'remove': []}
ENTITY_PERMS_MAPPINGS = {'view': VIEW,
                         'download': DOWNLOAD,
                         'edit': EDIT,
                         'edit_and_delete': EDIT_AND_DELETE,
                         'admin': ADMIN,
                         'remove': []}


def _set_permissions(syn, syn_obj, principalid, permission_level):
    """
    Helper function to set the ACL on entity or evaluation

    Args:
        syn: Synapse object
        syn_obj: An Evaluation or Entity
        permission_level: evaluation permissions: ["view", "submit",
                          "score", "admin"]
                          entity permissions: ["view","download","edit",
                          "edit_and_delete", "admin"]
                          'remove' can be specified to delete the permissions
        principalid: Synapse id of a user or team.
    """
    if isinstance(syn_obj, synapseclient.Evaluation):
        permission_level_mapping = EVALUATION_PERMS_MAPPINGS
    else:
        permission_level_mapping = ENTITY_PERMS_MAPPINGS

    if permission_level not in permission_level_mapping.keys():
        raise ValueError("permission_level must be one of these: {0}".format(
            ', '.join(permission_level_mapping.keys())))

    syn.setPermissions(syn_obj, principalId=principalid,
                       accessType=permission_level_mapping[permission_level])


def set_evaluation_permissions(syn, evaluation, principalid,
                               permission_level="view"):
    """
    Convenience function to set ACL on an entity for a user or team based on
    permission levels (view, download...)

    Args:
        syn: Synapse object
        evaluation: An Evaluation or Evaluation id
        principalid: Identifier of a user or group. To give anybody on the web
                     access, specify None.
        permission_level: Can be "view", "submit", "score", "admin", or
                          'remove'. If 'remove' is specified, the
                          permissions for the principalid is deleted.
                          Default is 'view'
    """
    # Get the evaluation to check for access / validity of entity
    evaluation = syn.getEvaluation(evaluation)
    _set_permissions(syn, evaluation, principalid, permission_level)


def set_entity_permissions(syn, entity, principalid,
                           permission_level="download"):
    """
    Convenience function to set ACL on an entity for a user or team based on
    permission levels (view, download...)

    Args:
        syn: Synapse object
        entity: An Entity or Synapse ID to lookup
        principalid: Identifier of a user or group. To give anybody on the web
                     access, specify None.
        permission_level: Can be "view", "download", "edit", "edit_and_delete",
                          "admin" or 'remove'. If 'remove' is specified, the
                          permissions for the principalid is deleted.
                          Default is 'download'
    """
    # Get the entity to check for access / validity of entity
    entity = syn.get(entity, downloadFile=False)
    _set_permissions(syn, entity, principalid, permission_level)


def get_user_entity_permissions(syn, entity):
    """Gets the list of permission that the caller has on a given Entity.
    https://rest-docs.synapse.org/rest/org/sagebionetworks/repo/model/auth/UserEntityPermissions.html

    Args:
        syn: Synapse connection
        entity: Synapse id or Entity

    Returns:
        UserEntityPermissions
    """
    synid = id_of(entity)
    permissions = syn.restGET("/entity/{}/permissions".format(synid))
    return permissions
