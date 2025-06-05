from io import StringIO
from unittest.mock import patch

import pytest
from accounts.management.commands.test_email import Command
from django.core.management import call_command
from django.test import override_settings

pytestmark = pytest.mark.django_db


class TestEmailCommand:
    """Test the test_email management command."""

    def test_command_help_text(self):
        """Test that the command has correct help text."""
        command = Command()
        assert command.help == "Test email configuration by sending a test email"

    def test_command_default_arguments(self):
        """Test command with default arguments."""
        out = StringIO()

        with patch(
            "accounts.management.commands.test_email.send_mail"
        ) as mock_send_mail:
            mock_send_mail.return_value = 1  # Success

            call_command("test_email", stdout=out)

            # Check that send_mail was called with default recipient
            mock_send_mail.assert_called_once()
            args, kwargs = mock_send_mail.call_args

            assert kwargs["subject"] == "Test Email from Feedit (Django)"
            assert "test email sent from Feedit" in kwargs["message"]
            assert kwargs["recipient_list"] == [
                "geraghtyglenn@gmail.com"
            ]  # default recipient
            assert not kwargs["fail_silently"]

    def test_command_custom_recipient(self):
        """Test command with custom recipient email."""
        out = StringIO()
        custom_email = "custom@example.com"

        with patch(
            "accounts.management.commands.test_email.send_mail"
        ) as mock_send_mail:
            mock_send_mail.return_value = 1  # Success

            call_command("test_email", "--to", custom_email, stdout=out)

            # Check that send_mail was called with custom recipient
            mock_send_mail.assert_called_once()
            args, kwargs = mock_send_mail.call_args

            assert kwargs["recipient_list"] == [custom_email]

    @override_settings(DEFAULT_FROM_EMAIL="noreply@feedit.online")
    def test_command_uses_settings_from_email(self):
        """Test command uses DEFAULT_FROM_EMAIL from settings."""
        out = StringIO()

        with patch(
            "accounts.management.commands.test_email.send_mail"
        ) as mock_send_mail:
            mock_send_mail.return_value = 1  # Success

            call_command("test_email", stdout=out)

            # Check that send_mail was called with correct from_email
            mock_send_mail.assert_called_once()
            args, kwargs = mock_send_mail.call_args

            assert kwargs["from_email"] == "noreply@feedit.online"

    def test_command_success_output(self):
        """Test command outputs success message when email is sent."""
        out = StringIO()

        with patch(
            "accounts.management.commands.test_email.send_mail"
        ) as mock_send_mail:
            mock_send_mail.return_value = 1  # Success

            call_command("test_email", stdout=out)

            output = out.getvalue()
            assert "Sending test email from" in output
            assert "Test email sent successfully!" in output

    def test_command_failure_output(self):
        """Test command outputs failure message when email sending fails."""
        out = StringIO()

        with patch(
            "accounts.management.commands.test_email.send_mail"
        ) as mock_send_mail:
            mock_send_mail.return_value = 0  # Failure

            call_command("test_email", stdout=out)

            output = out.getvalue()
            assert "Sending test email from" in output
            assert "Failed to send email. Result: 0" in output

    def test_command_exception_handling(self):
        """Test command handles exceptions gracefully."""
        out = StringIO()

        with patch(
            "accounts.management.commands.test_email.send_mail"
        ) as mock_send_mail:
            mock_send_mail.side_effect = Exception("SMTP connection failed")

            call_command("test_email", stdout=out)

            output = out.getvalue()
            assert "Sending test email from" in output
            assert "Error sending email: SMTP connection failed" in output

    def test_command_email_content(self):
        """Test that the email has correct subject and content."""
        out = StringIO()

        with patch(
            "accounts.management.commands.test_email.send_mail"
        ) as mock_send_mail:
            mock_send_mail.return_value = 1  # Success

            call_command("test_email", stdout=out)

            # Check email content
            mock_send_mail.assert_called_once()
            args, kwargs = mock_send_mail.call_args

            subject = kwargs["subject"]
            message = kwargs["message"]

            assert subject == "Test Email from Feedit (Django)"
            assert "This is a test email sent from Feedit" in message
            assert "MailerSend SMTP configuration" in message
            assert "Django" in message

    def test_command_argument_parsing(self):
        """Test that command correctly parses arguments."""
        command = Command()

        # Test argument parser setup
        parser = command.create_parser("test_email", "test_email")

        # Test default argument
        options = parser.parse_args([])
        assert options.to_email == "geraghtyglenn@gmail.com"

        # Test custom argument
        options = parser.parse_args(["--to", "custom@example.com"])
        assert options.to_email == "custom@example.com"

    def test_command_handle_method_directly(self):
        """Test calling the handle method directly."""
        command = Command()
        command.stdout = StringIO()

        with patch(
            "accounts.management.commands.test_email.send_mail"
        ) as mock_send_mail:
            mock_send_mail.return_value = 1  # Success

            # Test with default options
            options = {"to_email": "geraghtyglenn@gmail.com"}
            command.handle(**options)

            mock_send_mail.assert_called_once()

    def test_command_with_smtp_authentication_error(self):
        """Test command handles SMTP authentication errors."""
        out = StringIO()

        with patch(
            "accounts.management.commands.test_email.send_mail"
        ) as mock_send_mail:
            from smtplib import SMTPAuthenticationError

            mock_send_mail.side_effect = SMTPAuthenticationError(
                535, "Authentication failed"
            )

            call_command("test_email", stdout=out)

            output = out.getvalue()
            assert "Error sending email:" in output
            assert "Authentication failed" in output

    def test_command_with_smtp_server_error(self):
        """Test command handles SMTP server errors."""
        out = StringIO()

        with patch(
            "accounts.management.commands.test_email.send_mail"
        ) as mock_send_mail:
            from smtplib import SMTPServerDisconnected

            mock_send_mail.side_effect = SMTPServerDisconnected("Connection lost")

            call_command("test_email", stdout=out)

            output = out.getvalue()
            assert "Error sending email:" in output
            assert "Connection lost" in output

    def test_command_output_formatting(self):
        """Test that command output is properly formatted."""
        out = StringIO()

        with patch(
            "accounts.management.commands.test_email.send_mail"
        ) as mock_send_mail:
            mock_send_mail.return_value = 1  # Success

            with override_settings(DEFAULT_FROM_EMAIL="test@feedit.online"):
                call_command("test_email", "--to", "recipient@example.com", stdout=out)

            output = out.getvalue()

            # Check that output contains expected information
            assert (
                "Sending test email from test@feedit.online to recipient@example.com..."
                in output
            )
            assert "Test email sent successfully!" in output

    def test_command_fail_silently_false(self):
        """Test that command sets fail_silently=False for proper error reporting."""
        out = StringIO()

        with patch(
            "accounts.management.commands.test_email.send_mail"
        ) as mock_send_mail:
            mock_send_mail.return_value = 1  # Success

            call_command("test_email", stdout=out)

            # Verify fail_silently is False
            mock_send_mail.assert_called_once()
            args, kwargs = mock_send_mail.call_args
            assert not kwargs["fail_silently"]

    def test_command_integration_with_django_settings(self):
        """Test command integrates properly with Django settings."""
        out = StringIO()

        # Test with different email backend settings
        with override_settings(
            EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
            DEFAULT_FROM_EMAIL="console@feedit.online",
        ):
            with patch(
                "accounts.management.commands.test_email.send_mail"
            ) as mock_send_mail:
                mock_send_mail.return_value = 1  # Success

                call_command("test_email", stdout=out)

                # Check that settings are used correctly
                mock_send_mail.assert_called_once()
                args, kwargs = mock_send_mail.call_args
                assert (
                    kwargs["from_email"] == "console@feedit.online"
                )  # from_email from settings
