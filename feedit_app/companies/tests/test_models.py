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

    with mock.patch("secure_files.models.SecureFile.objects.filter") as mocked_filter:
        mocked_filter.return_value.first.return_value = "mocked_file"
        result = company.profile_picture
        assert result == "mocked_file"
        mocked_filter.assert_called_once()
