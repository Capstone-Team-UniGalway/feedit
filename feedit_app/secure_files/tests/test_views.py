import pytest
from accounts.tests.factories import UserFactory
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from secure_files.models import SecureFile
from secure_files.tests.factories import SecureFileFactory

pytestmark = pytest.mark.django_db


class TestSecureFileUploadView:
    def test_upload_file_requires_login(self, client):
        user = UserFactory()
        content_type = ContentType.objects.get_for_model(user.__class__)

        url = reverse(
            "secure_files:new",
            kwargs={"content_type_id": content_type.id, "object_id": user.id},
        )

        response = client.post(url)
        assert response.status_code == 302  # Redirects to login page

    def test_upload_file_success(self, client):
        user = UserFactory()
        client.force_login(user)

        content_type = ContentType.objects.get_for_model(user.__class__)

        url = reverse(
            "secure_files:new",
            kwargs={"content_type_id": content_type.id, "object_id": user.id},
        )

        file_data = SimpleUploadedFile(
            "profile.jpg", b"fake_image_data", content_type="image/jpeg"
        )

        response = client.post(url, {"file": file_data}, follow=True)

        assert response.status_code == 200

        # Check that the file was created
        assert SecureFile.objects.filter(
            content_type=content_type, object_id=user.id, uploaded_by=user
        ).exists()


class TestSecureFileDeleteView:
    def test_delete_file_requires_login(self, client):
        file = SecureFileFactory()

        url = reverse("secure_files:delete", kwargs={"file_id": file.id})

        response = client.post(url)
        assert response.status_code == 302  # Redirects to login page

    def test_delete_own_file(self, client):
        user = UserFactory()
        file = SecureFileFactory(content_object=user, uploaded_by=user)

        client.force_login(user)

        url = reverse("secure_files:delete", kwargs={"file_id": file.id})

        response = client.post(url, follow=True)

        assert response.status_code == 200

        # Check that the file was marked as deleted
        file.refresh_from_db()
        assert file.is_deleted

    def test_cannot_delete_others_file(self, client):
        user = UserFactory()
        other_user = UserFactory()
        file = SecureFileFactory(content_object=other_user, uploaded_by=other_user)

        client.force_login(user)

        url = reverse("secure_files:delete", kwargs={"file_id": file.id})

        with pytest.raises(Exception):  # PermissionDenied
            client.post(url)

        # Check that the file was not deleted
        file.refresh_from_db()
        assert not file.is_deleted


class TestSecureFileDownloadView:
    def test_download_file_requires_login(self, client):
        file = SecureFileFactory()

        url = reverse("secure_files:download", kwargs={"file_id": file.id})

        response = client.get(url)
        assert response.status_code == 302  # Redirects to login page

    def test_download_file(self, client):
        user = UserFactory()
        file = SecureFileFactory(content_object=user)

        client.force_login(user)

        url = reverse("secure_files:download", kwargs={"file_id": file.id})

        response = client.get(url)

        assert response.status_code == 200
        assert (
            response["Content-Disposition"] == f'attachment; filename="{file.filename}"'
        )
