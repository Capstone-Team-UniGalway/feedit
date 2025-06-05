from unittest import mock

import pytest
from accounts.tests.factories import UserFactory
from companies.models import Company

from .factories import CompanyFactory

pytestmark = pytest.mark.django_db


def test_company_factory_creates_valid_company():
    company = CompanyFactory()
    assert isinstance(company, Company)
    assert company.name.startswith("Test Company")
    assert company.country == "Ireland"
    assert company.employer is not None


def test_company_str_representation():
    company = CompanyFactory(name="Acme Corp", country="USA")
    assert str(company) == "Acme Corp (USA)"


def test_company_employer_link():
    user = UserFactory()
    company = CompanyFactory(employer=user)
    assert company.employer == user
    assert user.company == company


def test_profile_picture_property_returns_file_or_none():
    company = CompanyFactory()

    # Test case 1: No secure file found - should return placeholder
    with mock.patch("secure_files.models.SecureFile.objects.filter") as mocked_filter:
        mocked_filter.return_value.first.return_value = None
        result = company.profile_picture
        assert "company_placeholder.png" in result
        mocked_filter.assert_called_once()

    # Test case 2: Secure file found with file - should return secure file URL
    with (
        mock.patch("secure_files.models.SecureFile.objects.filter") as mocked_filter,
        mock.patch("secure_files.utils.get_secure_file_url") as mocked_get_url,
    ):

        # Create a mock secure file object with a file attribute
        mock_secure_file = mock.Mock()
        mock_secure_file.file = mock.Mock()  # Mock file exists
        mocked_filter.return_value.first.return_value = mock_secure_file
        mocked_get_url.return_value = "http://example.com/secure/company.jpg"

        result = company.profile_picture
        assert result == "http://example.com/secure/company.jpg"
        mocked_get_url.assert_called_once_with(mock_secure_file)
