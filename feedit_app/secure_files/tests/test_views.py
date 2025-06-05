import pytest
from accounts.tests.factories import UserFactory
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
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


class TestSecureFileDeleteView:
    def test_delete_file_requires_login(self, client):
        file = SecureFileFactory()

        url = reverse("secure_files:delete", kwargs={"file_id": file.id})

        response = client.post(url)
        assert response.status_code == 302  # Redirects to login page


class TestSecureFileDownloadView:
    def test_download_file_requires_login(self, client):
        # Create a file attached to a request (not user/company) which requires login
        from company_requests.tests.factories import RequestFactory

        request_obj = RequestFactory()
        file = SecureFileFactory(content_object=request_obj)

        url = reverse("secure_files:download", kwargs={"file_id": file.id})

        response = client.get(url)
        assert response.status_code == 403  # PermissionDenied for non-public files

    def test_download_file(self, client):
        user = UserFactory()
        file = SecureFileFactory(content_object=user)

        # No need to login for user profile pictures (they're public)
        url = reverse("secure_files:download", kwargs={"file_id": file.id})

        response = client.get(url)

        assert response.status_code == 200
        # Images use "inline" disposition, not "attachment"
        assert response["Content-Disposition"] == f'inline; filename="{file.filename}"'
