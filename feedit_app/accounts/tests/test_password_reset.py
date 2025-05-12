"""
Tests for password reset functionality.
"""
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

User = get_user_model()


class PasswordResetTest(TestCase):
    """Test the password reset functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
        )
        self.reset_url = reverse("account_reset_password")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_sends_email(self):
        """Test that the password reset form sends an email."""
        response = self.client.post(self.reset_url, {"email": "test@example.com"})
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Reset your password")
        self.assertEqual(mail.outbox[0].to, ["test@example.com"])

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_with_invalid_email(self):
        """Test that no email is sent for an invalid email address."""
        response = self.client.post(self.reset_url, {"email": "nonexistent@example.com"})
        self.assertEqual(response.status_code, 302)  # Should still redirect
        self.assertEqual(len(mail.outbox), 0)  # No email should be sent

    def test_password_reset_form_renders(self):
        """Test that the password reset form renders correctly."""
        response = self.client.get(self.reset_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reset your password")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_complete_flow(self):
        """Test the complete password reset flow."""
        # Request password reset
        response = self.client.post(self.reset_url, {"email": "test@example.com"})
        self.assertEqual(response.status_code, 302)  # Should redirect

        # Get the reset URL from the email
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        # Print debug info
        print(f"User ID: {self.user.pk}")
        print(f"UID: {uid}")
        print(f"Token: {token}")

        reset_confirm_url = reverse(
            "account_reset_password_from_key",
            kwargs={"uidb64": uid, "token": token},
        )
        print(f"Reset URL: {reset_confirm_url}")

        # First, visit the reset URL to get the form
        response = self.client.get(reset_confirm_url, follow=True)
        self.assertEqual(response.status_code, 200)

        # Get the redirect URL from the chain (should be the set-password URL)
        if response.redirect_chain:
            set_password_url = response.redirect_chain[0][0]
            print(f"Set password URL: {set_password_url}")
        else:
            set_password_url = reset_confirm_url
            print("No redirect occurred, using original URL")

        # Now post to the set-password URL
        response = self.client.post(
            set_password_url,
            {
                "new_password1": "newpassword123",
                "new_password2": "newpassword123",
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)  # Should eventually reach a 200 page after redirects

        # Print response details for debugging
        print(f"Response status: {response.status_code}")
        print(f"Response redirect chain: {response.redirect_chain}")
        print(f"Response content: {response.content[:500]}")

        # Refresh user from database to ensure we have the latest data
        self.user.refresh_from_db()

        # Verify password was changed by directly checking if it verifies
        self.assertTrue(
            self.user.check_password("newpassword123"),
            "Password was not updated in the database"
        )

        # Try to login with new password
        login_successful = self.client.login(
            email="test@example.com", password="newpassword123"
        )
        self.assertTrue(login_successful, "Login with new password failed")
