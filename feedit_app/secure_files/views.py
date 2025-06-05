import mimetypes

from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import (
    FileResponse,
    Http404,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from storages.backends.s3boto3 import S3Boto3Storage

from .forms import SecureFileForm
from .models import IMAGE_EXTENSIONS, SecureFile, get_allowed_content_types


class SecureFileUploadView(LoginRequiredMixin, View):
    """Handles secure file uploads with strict access control and object integrity."""

    def post(self, request, *args, **kwargs):
        print("FILES:", request.FILES)
        content_type_id = kwargs.get("content_type_id")
        object_id = kwargs.get("object_id")
        referer = request.META.get("HTTP_REFERER", "/")

        if not content_type_id or not object_id:
            return HttpResponseBadRequest("Missing required parameters.")

        content_type = get_object_or_404(ContentType, id=content_type_id)
        model = content_type.model
        if model not in get_allowed_content_types():
            return HttpResponseBadRequest("Invalid or disallowed content type.")

        model_class = content_type.model_class()
        content_object = get_object_or_404(
            model_class.objects.filter(is_deleted=False), id=object_id
        )

        # 🔐 Ensure we don't attach files to deleted objects
        # if getattr(content_object, "is_deleted", False):
        #     return HttpResponseBadRequest("Cannot upload to a deleted object.")

        if not self.has_upload_permission(request.user, model, content_object):
            return HttpResponseForbidden(
                "You do not have permission to upload files here."
            )

        form = SecureFileForm(
            request.POST,
            request.FILES,
            content_object=content_object,
            uploaded_by=request.user,
        )

        if form.is_valid():
            form.save()
            messages.success(request, "File uploaded successfully.")
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)

        return redirect(referer)

    def has_upload_permission(self, user, model, obj):
        """Upload permission rules per object type."""
        if user.is_superuser:
            return True
        if model == "user":
            return obj == user
        elif model == "company":
            return getattr(obj, "employer_id", None) == user.id
        elif model in ["thread", "request", "request_reply"]:
            return getattr(obj, "author_id", None) == user.id
        return False


class SecureFileDeleteView(LoginRequiredMixin, View):
    """Handles secure deletion of uploaded files with fine-grained permission rules."""

    def post(self, request, file_id, *args, **kwargs):
        referer = request.META.get("HTTP_REFERER", "/")

        secure_file = get_object_or_404(
            SecureFile.objects.filter(is_deleted=False), id=file_id
        )

        if not self.has_delete_permission(request.user, secure_file):
            raise PermissionDenied("You don't have permission to delete this file.")

        secure_file.delete()
        messages.success(request, "File deleted successfully.")
        return redirect(referer)

    def has_delete_permission(self, user, secure_file):
        """Applies ownership and role-based deletion rules per object type."""
        model = secure_file.content_type.model
        obj = secure_file.content_object

        if model not in get_allowed_content_types() or not obj:
            return False

        # 🔒 Only the user themselves can delete their own file
        if model == "user":
            return obj == user

        # 🔒 Only current employer can delete company files
        if model == "company":
            return getattr(obj, "employer_id", None) == user.id

        # 🧾 For threads, requests, replies: allow if author or file owner
        if model in ["thread", "request", "request_reply"]:
            return (
                getattr(obj, "author_id", None) == user.id
                or secure_file.uploaded_by_id == user.id
            )

        return user.is_superuser


class SecureFileDownloadView(View):
    """
    Secure file download view with per-model access control.
    Public for profile images; protected for other models.
    """

    def get(self, request, file_id, *args, **kwargs):
        secure_file = get_object_or_404(
            SecureFile.objects.filter(is_deleted=False), id=file_id
        )
        model = secure_file.content_type.model
        obj = secure_file.content_object
        user = request.user

        # Ensure the file exists and has a valid object
        if not secure_file.file or not obj:
            raise Http404("File not found")

        # Access control
        if model in ["user", "company"]:
            pass  # ✅ Public profile images
        elif user.is_superuser:
            pass  # ✅ Superuser override

        # All other models: enforce login
        elif not user.is_authenticated:
            raise PermissionDenied("Login required to access this file")

        # Threads: check thread visibility and membership
        elif model == "thread":
            company = obj.company
            if obj.visibility == "private":
                if user.workplace_id != company.id or user.type != "employee":
                    raise PermissionDenied("You cannot access this thread file.")
            elif obj.visibility == "internal":
                if (
                    user.workplace_id != company.id
                    and getattr(company, "employer_id", None) != user.id
                ):
                    raise PermissionDenied("You cannot access this thread file.")

        # Requests: author or employer
        elif model == "request":
            if (
                obj.author_id != user.id
                and getattr(obj.company, "employer_id", None) != user.id
            ):
                raise PermissionDenied("You cannot access this request file.")

        # Request replies: same as request
        elif model == "request_reply":
            request_author = obj.request.author
            company = obj.request.company
            if request_author_id := getattr(request_author, "id", None):
                if (
                    request_author_id != user.id
                    and getattr(company, "employer_id", None) != user.id
                ):
                    raise PermissionDenied("You cannot access this reply file.")
            else:
                raise PermissionDenied("Invalid request reference.")

        # Determine filename, content type and disposition
        filename = secure_file.filename
        extension = filename.rsplit(".", 1)[-1].lower()
        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = "application/octet-stream"

        is_image = extension in IMAGE_EXTENSIONS
        disposition = "inline" if is_image else "attachment"

        # Open file from appropriate storage
        try:
            if settings.ENVIRONMENT == "production":
                storage = S3Boto3Storage()
                file = storage.open(secure_file.file.name, "rb")
            else:
                file = open(secure_file.file.path, "rb")
        except (FileNotFoundError, ClientError):
            raise Http404("File not found")

        # Serve file with secure response
        response = FileResponse(file, content_type=content_type)
        response["Content-Disposition"] = f'{disposition}; filename="{filename}"'
        return response
