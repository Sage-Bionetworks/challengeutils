from synapseclient.exceptions import *

## Synapse user IDs of the challenge admins who will be notified by email
## about errors in the scoring script
ADMIN_USER_IDS = ['3324230']

def validate_submission(syn, evaluation, submission, public=False, admin=None):
    """
    Find the right validation function and validate the submission.

    :returns: (True, message) if validated, (False, message) if
              validation fails or throws exception
    """
    #Add in users to share this with
    share_with = []
    try:
        if public:
            message =  "Please make your private project (%s) public" % submission['entityId']
            share_with.append(message)
            ent = syn.getPermissions(submission['entityId'], 273948)
            assert "READ" in ent and "DOWNLOAD" in ent, message
            ent = syn.getPermissions(submission['entityId'])
            assert "READ" in ent, message
        if admin is not None:
            message =   "Please share your private directory (%s) with the Synapse user `%s` with `Can Download` permissions." % (submission['entityId'], admin)
            share_with.append(message)
            ent = syn.getPermissions(submission['entityId'], admin)
            assert "READ" in ent and "DOWNLOAD" in ent, message
    except SynapseHTTPError as e:
        if e.response.status_code == 403:
            raise AssertionError("\n".join(share_with))
        else:
            raise(e)
    return True, "Validated!"

