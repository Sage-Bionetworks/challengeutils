## Messages for challenge scoring script.

import string
import sys
import warnings


## Module level state. You'll need to set a synapse object at least
## before using this module.
syn = None
send_messages = True
send_notifications = True
acknowledge_receipt = False
dry_run = False


## Edit these URLs to point to your challenge and its support forum
defaults = dict(
    challenge_instructions_url = "https://www.synapse.org/#!Synapse:syn4224222/wiki/426788",
    support_forum_url = "https://www.synapse.org/#!Synapse:syn4224222/discussion/default",
    scoring_script = "DM Challenge Admins")

##---------------------------------------------------------
## Message templates:
## Edit to fit your challenge.
##---------------------------------------------------------

validation_failed_subject_template = "Validation error in submission to {queue_name}"
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

<p>If you have questions, please ask on the forums at {support_forum_url}.</p>

<p>Sincerely,<br>
{scoring_script}</p>
"""

validation_passed_subject_template = "Submission received to {queue_name}"
validation_passed_template = """\
<p>Hello {username},</p>

<p>We have received your write up to the {queue_name} and confirmed that it has the correct permissions.</p>

<p>submission name: <b>{submission_name}</b><br>
submission ID: <b>{submission_id}</b></p>

<p>If you have questions, please ask on the forums at {support_forum_url} or refer to the challenge \
instructions which can be found at {challenge_instructions_url}.</p>

<p>Sincerely,<br>
{scoring_script}</p>
"""

# scoring_succeeded_subject_template = "Scored submission to {queue_name}"
# scoring_succeeded_template = """\
# <p>Hello {username},</p>

# <p>Your submission \"{submission_name}\" (ID: {submission_id}) to the {queue_name} has been scored:</p>

# <blockquote><pre>
# {message}
# </pre></blockquote>

# <p>If you have questions, please ask on the forums at {support_forum_url}.</p>

# <p>Sincerely,<br>
# {scoring_script}</p>
# """

# scoring_error_subject_template = "Exception while scoring submission to {queue_name}"
# scoring_error_template = """\
# <p>Hello {username},</p>

# <p>Sorry, but we were unable to process your submission to the {queue_name}.</p>

# <p>Please refer to the challenge instructions which can be found at \
# {challenge_instructions_url} and to the error message below:</p>

# <p>submission name: <b>{submission_name}</b><br>
# submission ID: <b>{submission_id}</b></p>

# <blockquote><pre>
# {message}
# </pre></blockquote>

# <p>If you have questions, please ask on the forums at {support_forum_url}.</p>

# <p>Sincerely,<br>
# {scoring_script}</p>
# """

notification_subject_template = "Exception while scoring submission to {queue_name}"
error_notification_template = """\
<p>Hello Challenge Administrator,</p>

<p>The scoring script for {queue_name} encountered an error:</p>

<blockquote><pre>
{message}
</pre></blockquote>

<p>Sincerely,<br>
{scoring_script}</p>
"""


class DefaultingFormatter(string.Formatter):
    """
    Python's string.format has the annoying habit of raising a KeyError
    if you don't completely fill in the template. Let's do something a
    bit nicer.
    Adapted from: http://stackoverflow.com/a/19800610/199166
    """
    def get_value(self, key, args, kwds):
        if isinstance(key, str):
            value = kwds.get(key, defaults.get(key, None))
            if value is None:
                value = "{{{0}}}".format(key)
                warnings.warn("Missing template variable %s" % value)
            return value
        else:
            Formatter.get_value(key, args, kwds)

formatter = DefaultingFormatter()

##---------------------------------------------------------
## functions for sending various types of messages
##---------------------------------------------------------

def validation_failed(userIds, **kwargs):
    if send_messages:
        return send_message(userIds=userIds, 
                            subject_template=validation_failed_subject_template,
                            message_template=validation_failed_template,
                            kwargs=kwargs)

def validation_passed(userIds, **kwargs):
    if acknowledge_receipt:
        return send_message(userIds=userIds,
                            subject_template=validation_passed_subject_template,
                            message_template=validation_passed_template,
                            kwargs=kwargs)

def scoring_succeeded(userIds, **kwargs):
    if send_messages:
        return send_message(userIds=userIds,
                            subject_template=scoring_succeeded_subject_template,
                            message_template=scoring_succeeded_template,
                            kwargs=kwargs)

def scoring_error(userIds, **kwargs):
    if send_messages:
        return send_message(userIds=userIds,
                            subject_template=scoring_error_subject_template,
                            message_template=scoring_error_template,
                            kwargs=kwargs)

def error_notification(userIds, **kwargs):
    if send_notifications:
        return send_message(userIds=userIds,
                            subject_template=notification_subject_template,
                            message_template=error_notification_template,
                            kwargs=kwargs)

def send_message(userIds, subject_template, message_template, kwargs):
    subject = formatter.format(subject_template, **kwargs)
    message = formatter.format(message_template, **kwargs)
    if dry_run:
        print "\nDry Run: would have sent:"
        print subject
        print "-" * 60
        print message
        return None
    elif syn:
        response = syn.sendMessage(
            userIds=userIds,
            messageSubject=subject,
            messageBody=message,
            contentType="text/html")
        print "sent: ", unicode(response).encode('utf-8')
        return response
    else:
        sys.stderr.write("Can't send message. No Synapse object configured\n")



