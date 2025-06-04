from unittest.mock import Mock, patch

import pytest
from accounts.backends import SoftDeleteAwareBackend
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from .factories import UserFactory

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestSoftDeleteAwareBackend:
    """Test the SoftDeleteAwareBackend authentication backend."""

    def setup_method(self):
        self.backend = SoftDeleteAwareBackend()
        self.factory = RequestFactory()

    def test_authenticate_active_user_success(self):
        """Test authentication succeeds for active (non-deleted) user."""
        user = UserFactory(email="active@example.com")
        user.set_password("testpass123")
        user.save()

        request = self.factory.post("/login/")

        # Mock the parent backend's authenticate method to return the user
        with patch("accounts.backends.AllauthBackend.authenticate") as mock_auth:
            mock_auth.return_value = user

            result = self.backend.authenticate(
                request, email="active@example.com", password="testpass123"
            )

            assert result == user
            mock_auth.assert_called_once_with(
                request, email="active@example.com", password="testpass123"
            )

    def test_authenticate_deleted_user_blocked(self):
        """Test authentication fails for soft-deleted user."""
        user = UserFactory(email="deleted@example.com")
        user.set_password("testpass123")
        user.delete()  # Soft delete the user
        user.save()

        request = self.factory.post("/login/")

        # Mock the parent backend's authenticate method to return the deleted user
        with patch("accounts.backends.AllauthBackend.authenticate") as mock_auth:
            mock_auth.return_value = user

            result = self.backend.authenticate(
                request, email="deleted@example.com", password="testpass123"
            )

            assert result is None
            mock_auth.assert_called_once_with(
                request, email="deleted@example.com", password="testpass123"
            )

    def test_authenticate_invalid_credentials(self):
        """Test authentication fails for invalid credentials."""
        request = self.factory.post("/login/")

        # Mock the parent backend's authenticate method
        # to return None (invalid credentials)
        with patch("accounts.backends.AllauthBackend.authenticate") as mock_auth:
            mock_auth.return_value = None

            result = self.backend.authenticate(
                request, email="nonexistent@example.com", password="wrongpassword"
            )

            assert result is None
            mock_auth.assert_called_once_with(
                request, email="nonexistent@example.com", password="wrongpassword"
            )

    def test_authenticate_user_without_is_deleted_attribute(self):
        """Test authentication handles users without is_deleted attribute gracefully."""
        # Create a mock user without is_deleted attribute
        mock_user = Mock()
        del mock_user.is_deleted  # Remove the attribute

        request = self.factory.post("/login/")

        # Mock the parent backend's authenticate method to return the mock user
        with patch("accounts.backends.AllauthBackend.authenticate") as mock_auth:
            mock_auth.return_value = mock_user

            result = self.backend.authenticate(
                request, email="test@example.com", password="testpass123"
            )

            # Should return the user since getattr returns False for missing attribute
            assert result == mock_user

    def test_authenticate_user_with_false_is_deleted(self):
        """Test authentication succeeds for user with is_deleted=False."""
        user = UserFactory(email="active@example.com")
        user.set_password("testpass123")
        user.is_deleted = False
        user.save()

        request = self.factory.post("/login/")

        # Mock the parent backend's authenticate method to return the user
        with patch("accounts.backends.AllauthBackend.authenticate") as mock_auth:
            mock_auth.return_value = user

            result = self.backend.authenticate(
                request, email="active@example.com", password="testpass123"
            )

            assert result == user

    def test_authenticate_user_with_true_is_deleted(self):
        """Test authentication fails for user with is_deleted=True."""
        user = UserFactory(email="deleted@example.com")
        user.set_password("testpass123")
        user.is_deleted = True
        user.save()

        request = self.factory.post("/login/")

        # Mock the parent backend's authenticate method to return the user
        with patch("accounts.backends.AllauthBackend.authenticate") as mock_auth:
            mock_auth.return_value = user

            result = self.backend.authenticate(
                request, email="deleted@example.com", password="testpass123"
            )

            assert result is None

    def test_authenticate_with_no_request(self):
        """Test authentication works without request object."""
        user = UserFactory(email="active@example.com")
        user.set_password("testpass123")
        user.save()

        # Mock the parent backend's authenticate method to return the user
        with patch("accounts.backends.AllauthBackend.authenticate") as mock_auth:
            mock_auth.return_value = user

            result = self.backend.authenticate(
                None, email="active@example.com", password="testpass123"  # No request
            )

            assert result == user

    def test_authenticate_with_kwargs_credentials(self):
        """Test authentication works with keyword arguments."""
        user = UserFactory(email="active@example.com")
        user.set_password("testpass123")
        user.save()

        request = self.factory.post("/login/")

        # Mock the parent backend's authenticate method to return the user
        with patch("accounts.backends.AllauthBackend.authenticate") as mock_auth:
            mock_auth.return_value = user

            result = self.backend.authenticate(
                request,
                username="active@example.com",  # Different credential name
                password="testpass123",
            )

            assert result == user
            mock_auth.assert_called_once_with(
                request, username="active@example.com", password="testpass123"
            )

    def test_authenticate_preserves_parent_behavior(self):
        """Test that the backend preserves all parent authentication behavior."""
        request = self.factory.post("/login/")

        # Test that all arguments are passed through correctly
        with patch("accounts.backends.AllauthBackend.authenticate") as mock_auth:
            mock_auth.return_value = None

            # Call with various argument combinations
            self.backend.authenticate(request, email="test@example.com")
            self.backend.authenticate(request, username="test", password="pass")
            self.backend.authenticate(request, token="abc123")

            # Verify all calls were made to parent
            assert mock_auth.call_count == 3

    def test_backend_inheritance(self):
        """Test that the backend properly inherits from AllauthBackend."""
        from allauth.account.auth_backends import (
            AuthenticationBackend as AllauthBackend,
        )

        assert isinstance(self.backend, AllauthBackend)

        # Test that other methods from parent are available
        assert hasattr(self.backend, "get_user")
        assert hasattr(self.backend, "user_can_authenticate")

    def test_authenticate_exception_handling(self):
        """Test authentication handles exceptions from parent backend gracefully."""
        request = self.factory.post("/login/")

        # Mock the parent backend to raise an exception
        with patch("accounts.backends.AllauthBackend.authenticate") as mock_auth:
            mock_auth.side_effect = Exception("Database error")

            # The exception should propagate (not caught by our backend)
            with pytest.raises(Exception, match="Database error"):
                self.backend.authenticate(
                    request, email="test@example.com", password="testpass123"
                )
