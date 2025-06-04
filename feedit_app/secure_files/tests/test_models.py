import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from secure_files.models import SecureFile
from .factories import SecureFileFactory
from accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_secure_file_factory_creates_valid_instance():
    file = SecureFileFactory()
    assert isinstance(file, SecureFile)
    assert file.content_type.model == "user"
    assert file.filename == "profile.jpg"


def test_secure_file_enforces_allowed_content_types():
    file = SecureFileFactory.build()
    file.content_type = ContentType.objects.get_for_model(SecureFile)  # not allowed
    with pytest.raises(ValidationError):
        file.full_clean()


def test_secure_file_rejects_non_image_for_user():
    file = SecureFileFactory.build(
        file=SimpleUploadedFile("document.pdf", b"data", content_type="application/pdf")
    )
    file.filename = "document.pdf"
    with pytest.raises(ValidationError):
        file.full_clean()


def test_secure_file_allows_non_image_for_request():
    from company_requests.tests.factories import RequestFactory

    file = SecureFileFactory.build(
        content_object=RequestFactory(),
        file=SimpleUploadedFile("report.pdf", b"data", content_type="application/pdf"),
        filename="report.pdf",
    )
    file.full_clean()  # Should pass


def test_secure_file_is_profile_picture_property():
    file = SecureFileFactory(content_object=UserFactory())
    assert file.is_profile_picture is True

    file.content_type = ContentType.objects.get_for_model(SecureFile)
    assert file.is_profile_picture is False
