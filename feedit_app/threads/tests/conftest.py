from unittest.mock import PropertyMock, patch

import pytest
from django.contrib.auth.models import AnonymousUser


@pytest.fixture(autouse=True)
def mock_anonymous_user_attributes():
    """Mock AnonymousUser attributes to prevent AttributeError in views."""

    # Mock workplace attribute for AnonymousUser
    with patch.object(
        AnonymousUser, "workplace", new_callable=PropertyMock
    ) as mock_workplace:
        mock_workplace.return_value = None

        # Mock type attribute for AnonymousUser
        with patch.object(
            AnonymousUser, "type", new_callable=PropertyMock
        ) as mock_type:
            mock_type.return_value = None

            # Mock company attribute for AnonymousUser
            with patch.object(
                AnonymousUser, "company", new_callable=PropertyMock
            ) as mock_company:
                mock_company.return_value = None

                yield


@pytest.fixture(autouse=True)
def mock_user_test_func():
    """Mock user_test_func to return True for
    FullyActivatedUserMixin in test environment."""
    from app.mixins import FullyActivatedUserMixin

    with patch.object(FullyActivatedUserMixin, "user_test_func") as mock_func:
        mock_func.return_value = True
        yield
