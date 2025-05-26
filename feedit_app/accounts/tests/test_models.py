import pytest
from accounts.models import User
from .factories import UserFactory
from companies.tests.factories import CompanyFactory
from django.core.exceptions import ValidationError

pytestmark = pytest.mark.django_db


def test_user_factory_creates_valid_user():
    user = UserFactory()
    assert isinstance(user, User)
    assert user.email.startswith("user")
    assert user.check_password("testpass123")
    assert user.type == User.UserType.EMPLOYEE


def test_user_str_returns_email():
    user = UserFactory(email="strcheck@feedit.online")
    assert str(user) == "strcheck@feedit.online"


def test_get_full_name():
    user = UserFactory(first_name="Ada", last_name="Lovelace")
    assert user.get_full_name() == "Ada Lovelace"


def test_create_user_via_manager():
    user = User.objects.create_user(
        email="manager@feedit.online",
        password="securepass123",
        first_name="Manager",
        last_name="Test",
    )
    assert user.email == "manager@feedit.online"
    assert user.check_password("securepass123")
    assert not user.is_superuser
    assert not user.is_staff


def test_create_superuser_via_manager():
    admin = User.objects.create_superuser(
        email="admin@feedit.online",
        password="adminpass123",
        first_name="Admin",
        last_name="User",
    )
    assert admin.is_superuser
    assert admin.is_staff
    assert admin.check_password("adminpass123")


def test_invalid_email_validation():
    user = UserFactory.build(email="bad-email")
    with pytest.raises(ValidationError):
        user.full_clean()


def test_soft_delete_sets_flags():
    user = UserFactory()
    user.delete()
    assert user.is_deleted
    assert user.deleted_at is not None


def test_user_workplace_link():
    company = CompanyFactory()
    user = UserFactory(workplace=company)

    assert user.workplace == company
    assert user in company.employees.all()


def test_profile_picture_property_returns_file_or_none():
    user = UserFactory()

    # Test when no file exists
    result = user.profile_picture
    assert result == "/assets/images/user_placeholder.png"

    # Test when file exists - just verify it doesn't return the placeholder
    from secure_files.tests.factories import SecureFileFactory
    SecureFileFactory(content_object=user)

    result = user.profile_picture
    # Should return the file URL, not the placeholder
    assert result != "/assets/images/user_placeholder.png"
    assert "profile" in result and ".jpg" in result
