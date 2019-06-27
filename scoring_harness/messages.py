# Messages for challenge scoring script.
DEFAULTS = dict(
    challenge_instructions_url="https://www.synapse.org/{challenge_synid}",
    support_forum_url="https://www.synapse.org/#!Synapse:{challenge_synid}/discussion/default",
    scoring_script="The Challenge Admin")

# ---------------------------------------------------------
# Message templates:
# Edit to fit your challenge.
# ---------------------------------------------------------

validation_failed_subject_template = \
    "Validation error in submission to {queue_name}"
validation_failed_template = """\
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

validation_passed_subject_template = "Submission received to {queue_name}"
validation_passed_template = """\
<p>Hello {username},</p>

<p>We have received your submission to the {queue_name} and confirmed that it is correctly formatted.</p>

<p>submission name: <b>{submission_name}</b><br>
submission ID: <b>{submission_id}</b></p>

<p>If you have questions, please ask on the forums at {support_forum_url} or refer to the challenge \
instructions which can be found at {challenge_instructions_url}.</p>

<p>Sincerely,<br>
{scoring_script}</p>
"""

scoring_succeeded_subject_template = "Scored submission to {queue_name}"
scoring_succeeded_template = """\
<p>Hello {username},</p>

<p>Your submission \"{submission_name}\" (ID: {submission_id}) to the {queue_name} has been scored:</p>

<blockquote><pre>
{message}
</pre></blockquote>

<p>If you have questions, please ask on the forums at {support_forum_url}.</p>

<p>Sincerely,<br>
{scoring_script}</p>
"""

scoring_error_subject_template = \
    "Exception while scoring submission to {queue_name}"
scoring_error_template = """\
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

notification_subject_template = \
    "Exception while scoring submission to {queue_name}"
error_notification_template = """\
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
                 userIds,
                 subject_template,
                 message_template,
                 dry_run,
                 kwargs):
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
    else:
        response = syn.sendMessage(
            userIds=userIds,
            messageSubject=subject,
            messageBody=message,
            contentType="text/html")
        print("sent: ", response)
        return response


def validation_failed(syn, userIds, send_messages, dry_run, **kwargs):
    if send_messages:
        return send_message(
            syn=syn,
            userIds=userIds,
            subject_template=validation_failed_subject_template,
            message_template=validation_failed_template,
            dry_run=dry_run,
            kwargs=kwargs)


def scoring_error(syn, userIds, send_messages, dry_run, **kwargs):
    if send_messages:
        return send_message(syn,
                            userIds=userIds,
                            subject_template=scoring_error_subject_template,
                            message_template=scoring_error_template,
                            dry_run=dry_run,
                            kwargs=kwargs)


def validation_passed(syn, userIds, acknowledge_receipt, dry_run, **kwargs):
    if acknowledge_receipt:
        return send_message(
            syn=syn,
            userIds=userIds,
            subject_template=validation_passed_subject_template,
            message_template=validation_passed_template,
            dry_run=dry_run,
            kwargs=kwargs)


def scoring_succeeded(syn, userIds, send_messages, dry_run, **kwargs):
    if send_messages:
        return send_message(
            syn=syn,
            userIds=userIds,
            subject_template=scoring_succeeded_subject_template,
            message_template=scoring_succeeded_template,
            dry_run=dry_run,
            kwargs=kwargs)


def error_notification(syn, userIds, send_notifications, dry_run, **kwargs):
    if send_notifications:
        return send_message(
            syn=syn,
            userIds=userIds,
            subject_template=notification_subject_template,
            message_template=error_notification_template,
            dry_run=dry_run,
            kwargs=kwargs)
