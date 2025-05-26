import pytest
from django.test.utils import override_settings
from unittest.mock import patch


@pytest.fixture(scope="function", autouse=True)
def test_settings():
    """
    Configure Django settings for tests.

    This fixture automatically applies to all tests and ensures that:
    1. testserver is allowed as a host (required for Django test client)
    2. MFA enforcement is disabled to prevent unexpected redirects in tests
    3. Factory sequences are reset to avoid conflicts
    4. FullyActivatedUserMixin always allows access during tests
    """

    # Reset factory sequences to avoid conflicts between tests
    from accounts.tests.factories import UserFactory, FullyActivatedUserFactory
    from app.mixins import FullyActivatedUserMixin
    UserFactory.reset_sequence()
    FullyActivatedUserFactory.reset_sequence(force=True)

    # Mock FullyActivatedUserMixin to allow access for authenticated users during tests
    with patch.object(FullyActivatedUserMixin, 'user_test_func', lambda self: self.request.user.is_authenticated):
        with override_settings(
            # Allow testserver for Django test client
            ALLOWED_HOSTS=['localhost', 'testserver'],
            # Disable MFA enforcement during tests
            ACCOUNT_MFA_ENFORCE_AFTER_LOGIN=False,
            ACCOUNT_MFA_ENABLED=False,
            # Use Django's default authentication backend for tests
            AUTHENTICATION_BACKENDS=[
                'django.contrib.auth.backends.ModelBackend',
            ],
        ):
            yield
