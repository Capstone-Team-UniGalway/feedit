"""
Custom email backend for MailerSend integration.
"""
import json
import urllib.request
import urllib.error
import urllib.parse
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address


class MailerSendEmailBackend(BaseEmailBackend):
    """
    A Django email backend for MailerSend using urllib instead of requests.
    """
    def __init__(self, api_key=None, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.api_key = api_key or settings.MAILERSEND_API_KEY
        self.api_url = "https://api.mailersend.com/v1/email"

    def send_messages(self, email_messages):
        """
        Send multiple email messages.
        """
        if not email_messages:
            return 0

        # Send all messages
        sent_count = 0
        for message in email_messages:
            sent_count += self._send(message)

        return sent_count

    def _send(self, email_message):
        """
        Send a single email message.
        """
        if not email_message.recipients():
            return 0

        # Prepare the message
        from_email = sanitize_address(email_message.from_email, email_message.encoding)
        if not from_email:
            from_email = settings.MAILERSEND_VERIFICATION_SENDER_EMAIL

        # Extract the name and email from the from_email
        from_name = ""
        from_address = from_email
        if "<" in from_email and ">" in from_email:
            from_name, from_address = from_email.split("<", 1)
            from_name = from_name.strip()
            from_address = from_address.strip(">").strip()

        # Prepare recipients
        recipients = []
        for recipient in email_message.recipients():
            recipient = sanitize_address(recipient, email_message.encoding)
            recipients.append({"email": recipient})

        # Prepare the payload
        payload = {
            "from": {
                "email": from_address,
                "name": from_name or "Feedit"
            },
            "to": recipients,
            "subject": email_message.subject,
        }

        # Handle content (plain text and HTML)
        if email_message.content_subtype == "html":
            payload["html"] = email_message.body
        else:
            payload["text"] = email_message.body

            # If there's an HTML alternative, include it
            for alt in email_message.alternatives:
                content, mimetype = alt
                if mimetype == "text/html":
                    payload["html"] = content
                    break

        # Send the request using urllib
        try:
            # Convert payload to JSON
            data = json.dumps(payload).encode('utf-8')

            # Create request
            req = urllib.request.Request(self.api_url, data=data, method='POST')

            # Add headers
            req.add_header('Content-Type', 'application/json')
            req.add_header('X-Requested-With', 'XMLHttpRequest')
            req.add_header('Authorization', f'Bearer {self.api_key}')

            # Send request
            with urllib.request.urlopen(req) as response:
                status = response.status
                if status not in (200, 201, 202):
                    if not self.fail_silently:
                        response_text = response.read().decode('utf-8')
                        error_msg = f"MailerSend API error: {status} - {response_text}"
                        raise Exception(error_msg)
                    return 0
                return 1

        except urllib.error.URLError as e:
            if not self.fail_silently:
                raise
            return 0
        except Exception as e:
            if not self.fail_silently:
                raise
            return 0
