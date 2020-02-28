
'''
Message templates
'''

# Messages for challenge scoring script.
DEFAULTS = dict(challenge_instructions_url="https://www.synapse.org/#!Synapse:{challenge_synid}",
                support_forum_url="https://www.synapse.org/#!Synapse:{challenge_synid}/discussion/default", #pylint: disable=line-too-long
                scoring_script="The Challenge Admin")

VALIDATION_FAILED_SUBJECT_TEMPLATE = "Validation error in submission to {queue_name}"
VALIDATION_FAILED_TEMPLATE = """\
<p>Hello {username},</p>

<p>Sorry, but we were unable to validate your submission to the {queue_name}.</p>

<p>Please refer to the challenge instructions which can be found at \
{challenge_instructions_url} and to the error message below:</p>

<p>submission name: <b>{submission_name}</b><br>
submission ID: <b>{submission_id}</b></p>

<blockquote><pre>
{message}
</pre></blockquote>

<p>If you have questions, please ask on the discussion tab at {support_forum_url}.</p>

<p>Sincerely,<br>
{scoring_script}</p>
"""

VALIDATION_PASSED_SUBJECT_TEMPLATE = "Submission received to {queue_name}"
VALIDATION_PASSED_TEMPLATE = """\
<p>Hello {username},</p>

<p>We have received your submission to the {queue_name} and confirmed that it is correctly formatted.</p>

<p>submission name: <b>{submission_name}</b><br>
submission ID: <b>{submission_id}</b></p>

<p>If you have questions, please ask on the forums at {support_forum_url} or refer to the challenge \
instructions which can be found at {challenge_instructions_url}.</p>

<p>Sincerely,<br>
{scoring_script}</p>
"""

SCORING_SUCEEDED_SUBJECT_TEMPLATE = "Scored submission to {queue_name}"
SCORING_SUCEEDED_TEMPLATE = """\
<p>Hello {username},</p>

<p>Your submission \"{submission_name}\" (ID: {submission_id}) to the {queue_name} has been scored:</p>

<blockquote><pre>
{message}
</pre></blockquote>

<p>If you have questions, please ask on the forums at {support_forum_url}.</p>

<p>Sincerely,<br>
{scoring_script}</p>
"""

SCORING_ERROR_SUBJECT_TEMPLATE = "Exception while scoring submission to {queue_name}"
SCORING_ERROR_TEMPLATE = """\
<p>Hello {username},</p>
<p>Sorry, but we were unable to process your submission to the {queue_name}.</p>
<p>Please refer to the challenge instructions which can be found at \
{challenge_instructions_url} and to the error message below:</p>
<p>submission name: <b>{submission_name}</b><br>
submission ID: <b>{submission_id}</b></p>
<blockquote><pre>
{message}
</pre></blockquote>
<p>If you have questions, please ask on the forums at {support_forum_url}.</p>
<p>Sincerely,<br>
{scoring_script}</p>
"""

ERROR_NOTIFICATION_SUBJECT_TEMPLATE = "Exception while scoring submission to {queue_name}"
ERROR_NOTIFICATION_TEMPLATE = """\
<p>Hello Challenge Administrator,</p>

<p>The scoring script for {queue_name} encountered an error:</p>

<blockquote><pre>
{message}
</pre></blockquote>

<p>Sincerely,<br>
{scoring_script}</p>
"""


class DefaultFormatter(dict):
    """
    Python's string.format has the annoying habit of raising a KeyError
    if you don't completely fill in the template. Let's do something a
    bit nicer.
    Adapted from: http://stackoverflow.com/a/19800610/199166
    """
    def __missing__(self, key):
        return '{'+key+'}'


# ---------------------------------------------------------
# functions for sending various types of messages
# ---------------------------------------------------------
def send_message(syn,
                 userids,
                 subject_template,
                 message_template,
                 dry_run,
                 kwargs):
    '''
    Sends emails to participants
    '''
    subject = subject_template.format_map(DefaultFormatter(DEFAULTS))
    subject = subject.format_map(DefaultFormatter(kwargs))
    message = message_template.format_map(DefaultFormatter(DEFAULTS))
    message = message.format_map(DefaultFormatter(kwargs))
    if dry_run:
        print("\nDry Run: would have sent:")
        print(subject)
        print("-" * 60)
        print(message)
        return None
    response = syn.sendMessage(userIds=userids,
                               messageSubject=subject,
                               messageBody=message,
                               contentType="text/html")
    print("sent: ", response)
    return response


def validation_failed(syn, userids, send_messages, dry_run, **kwargs):
    '''
    Helper function to send validation failed email
    '''
    if send_messages:
        return send_message(syn=syn,
                            userids=userids,
                            subject_template=VALIDATION_FAILED_SUBJECT_TEMPLATE,
                            message_template=VALIDATION_FAILED_TEMPLATE,
                            dry_run=dry_run,
                            kwargs=kwargs)


def scoring_error(syn, userids, send_messages, dry_run, **kwargs):
    '''
    Helper function to send scoring error email
    '''
    if send_messages:
        return send_message(syn,
                            userids=userids,
                            subject_template=SCORING_ERROR_SUBJECT_TEMPLATE,
                            message_template=SCORING_ERROR_TEMPLATE,
                            dry_run=dry_run,
                            kwargs=kwargs)


def validation_passed(syn, userids, acknowledge_receipt, dry_run, **kwargs):
    '''
    Helper function to send validation passed email
    '''
    if acknowledge_receipt:
        return send_message(syn=syn,
                            userids=userids,
                            subject_template=VALIDATION_PASSED_SUBJECT_TEMPLATE,
                            message_template=VALIDATION_PASSED_TEMPLATE,
                            dry_run=dry_run,
                            kwargs=kwargs)


def scoring_succeeded(syn, userids, send_messages, dry_run, **kwargs):
    '''
    Helper function to send scoring succeeded emails
    '''
    if send_messages:
        return send_message(syn=syn,
                            userids=userids,
                            subject_template=SCORING_SUCEEDED_SUBJECT_TEMPLATE,
                            message_template=SCORING_SUCEEDED_TEMPLATE,
                            dry_run=dry_run,
                            kwargs=kwargs)


def error_notification(syn, userids, send_notifications, dry_run, **kwargs):
    '''
    Helper function to send error notification emails
    '''
    if send_notifications:
        return send_message(syn=syn,
                            userids=userids,
                            subject_template=ERROR_NOTIFICATION_SUBJECT_TEMPLATE,
                            message_template=ERROR_NOTIFICATION_TEMPLATE,
                            dry_run=dry_run,
                            kwargs=kwargs)
