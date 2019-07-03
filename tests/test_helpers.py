from mock import patch
import synapseclient
import challengeutils.helpers
import challengeutils.utils
EVALUATION_ID = 111111
OBJECTID = "99999"
syn = synapseclient.Synapse()


def test_make_submission_status_invalid():
    uri = ("select objectId from evaluation_{evalid} "
           "where status == 'ACCEPTED' and "
           "prediction_file_status == 'INVALID'".format(evalid=EVALUATION_ID))
    with patch.object(challengeutils.utils,
                      "evaluation_queue_query",
                      return_value=[{"objectId": OBJECTID}]) as patch_eval_queue,\
        patch.object(challengeutils.utils,
                     "change_submission_status") as patch_change_status:
        challengeutils.helpers.make_submission_status_invalid(syn, EVALUATION_ID)
        patch_eval_queue.assert_called_once_with(syn, uri)
        patch_change_status.assert_called_once_with(syn, OBJECTID, 'INVALID')
