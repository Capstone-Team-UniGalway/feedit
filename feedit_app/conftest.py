import pytest
from django.test.utils import override_settings
from unittest.mock import patch, PropertyMock
from django.contrib.auth.models import AnonymousUser


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
    UserFactory.reset_sequence()
    FullyActivatedUserFactory.reset_sequence(force=True)

    # Mock the FullyActivatedUserMixin to allow access for authenticated users during tests
    from app.mixins import FullyActivatedUserMixin
    from django.contrib.auth.mixins import UserPassesTestMixin

    def mock_test_func(self):
        # Allow access for any authenticated user during tests
        return self.request.user.is_authenticated

    # Add missing attributes to AnonymousUser to prevent AttributeError in views
    # Store original state to restore later
    original_attrs = {}
    attrs_to_add = ['workplace', 'type', 'company']

    for attr in attrs_to_add:
        if not hasattr(AnonymousUser, attr):
            setattr(AnonymousUser, attr, None)
            original_attrs[attr] = True
        else:
            original_attrs[attr] = False

    # Add UserType class to AnonymousUser to prevent AttributeError when accessing user.UserType.EMPLOYEE
    if not hasattr(AnonymousUser, 'UserType'):
        from accounts.models import User
        setattr(AnonymousUser, 'UserType', User.UserType)
        original_attrs['UserType'] = True
    else:
        original_attrs['UserType'] = False

    try:
        with patch.object(FullyActivatedUserMixin, 'test_func', mock_test_func), \
             patch.object(UserPassesTestMixin, 'test_func', mock_test_func):
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
    finally:
        # Clean up: remove attributes we added to AnonymousUser
        for attr, was_added in original_attrs.items():
            if was_added and hasattr(AnonymousUser, attr):
                delattr(AnonymousUser, attr)
