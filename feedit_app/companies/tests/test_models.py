import pytest
from companies.models import Company
from .factories import CompanyFactory
from accounts.tests.factories import UserFactory

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

    # Test when no file exists
    result = company.profile_picture
    assert result == "/assets/images/company_placeholder.png"

    # Test when file exists - just verify it doesn't return the placeholder
    from secure_files.tests.factories import SecureFileFactory
    SecureFileFactory(content_object=company)

    result = company.profile_picture
    # Should return the file URL, not the placeholder
    assert result != "/assets/images/company_placeholder.png"
    assert "profile" in result and ".jpg" in result
