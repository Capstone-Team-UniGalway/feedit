"""
Custom email backend for MailerSend integration.
"""
import json
import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address


class MailerSendEmailBackend(BaseEmailBackend):
    """
    A Django email backend for MailerSend.
    """
    def __init__(self, api_key=None, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.api_key = api_key or settings.MAILERSEND_API_KEY
        self.api_url = "https://api.mailersend.com/v1/email"
        self.session = None

    def open(self):
        """
        Create a session for sending emails.
        """
        if self.session:
            return False
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Authorization': f'Bearer {self.api_key}'
        })
        return True

    def close(self):
        """
        Close the session.
        """
        if self.session:
            self.session.close()
            self.session = None

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
        
        # Send the request
        try:
            response = self.session.post(self.api_url, json=payload)
            if response.status_code not in (200, 201, 202):
                if not self.fail_silently:
                    error_msg = f"MailerSend API error: {response.status_code} - {response.text}"
                    raise Exception(error_msg)
                return 0
            return 1
        except Exception as e:
            if not self.fail_silently:
                raise
            return 0

    def send_messages(self, email_messages):
        """
        Send multiple email messages.
        """
        if not email_messages:
            return 0
        
        # Open the connection
        self.open()
        
        # Send all messages
        sent_count = 0
        try:
            for message in email_messages:
                sent_count += self._send(message)
        finally:
            # Close the connection
            self.close()
        
        return sent_count
