from app.base_model import BaseModel
from companies.models import Company
from company_requests.models import Request, RequestReply
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from threads.models import Thread
from django.utils.module_loading import import_string

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_MODELS = [get_user_model(), Company, Thread, Request, RequestReply]
# ALLOWED_CONTENT_TYPES = [
#     ContentType.objects.get_for_model(model).model for model in ALLOWED_MODELS
# ]
IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]


def get_allowed_content_types():
    return [ContentType.objects.get_for_model(model).model for model in ALLOWED_MODELS]


def validate_file_size(file):
    if file.size > MAX_FILE_SIZE:
        raise ValidationError("Max file size is 10MB.")


def upload_to(instance, filename):
    model = instance.content_type.model
    obj = instance.content_object

    if not obj or not hasattr(obj, "id") or not obj.id:
        return f"unresolved/{model}/unsaved/{filename}"

    # User and company profile pictures
    if model in ["user", "company"]:
        return f"attachments/{model}/{obj.id}/{filename}"

    # Thread or request files under a company
    if model in ["thread", "request"] and hasattr(obj, "company_id"):
        return f"attachments/company/{obj.company_id}/{model}/{obj.id}/{filename}"

    # Request reply files
    if model == "requestreply" and hasattr(obj, "request"):
        company_id = getattr(obj.request.company, "id", "unknown")
        return (
            f"attachments/company/{company_id}/request/{obj.request.id}/"
            f"replies/{obj.id}/{filename}"
        )

    # Fallback
    return f"unresolved/{model}/{obj.id or 'unsaved'}/{filename}"


class SecureFile(BaseModel):
    """Generic file attachment system."""

    # Generic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    file = models.FileField(
        upload_to=upload_to,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf", "docx", "jpg", "png", "jpeg", "webp", "xlsx"]
            ),
            validate_file_size,
        ],
    )
    filename = models.CharField(max_length=255, editable=False)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_files",
    )
    size = models.PositiveIntegerField(editable=False)

    def save(self, *args, **kwargs):
        # ✅ Force correct storage backend in production
        if settings.ENVIRONMENT == "production" and not isinstance(
            self.file.storage, import_string(settings.DEFAULT_FILE_STORAGE)
        ):
            storage_class = import_string(settings.DEFAULT_FILE_STORAGE)
            self.file.storage = storage_class()
            print(f"📦 Forcing file storage to {self.file.storage.__class__.__name__}")

        model = self.content_type.model

        # 🔒 Skip validation if part of soft-deletion
        if getattr(self, "_suppress_validation", False):
            return super().save(*args, **kwargs)

        # ✅ Enforce allowed content types
        if model not in get_allowed_content_types():
            raise ValidationError(
                f"Attachments to '{self.content_type.name}' are not allowed."
            )

        if not self.file or not getattr(self.file, "name", None):
            raise ValidationError("Uploaded file is missing or invalid.")

        # ✅ Only allow image files except for request/request_reply
        extension = self.file.name.rsplit(".", 1)[-1].lower()
        if (
            model not in ["request", "requestreply"]
            and extension not in IMAGE_EXTENSIONS
        ):
            raise ValidationError(
                f"Only image files are allowed for '{model}' attachments."
            )

        # ✅ One-file-only enforcement for User/Company
        if model in ["user", "company"]:
            existing = (
                SecureFile.objects.filter(
                    content_type=self.content_type,
                    object_id=self.object_id,
                    is_deleted=False,
                )
                .exclude(pk=self.pk)
                .first()
            )

            if existing:
                if existing.file:
                    existing.file.delete(save=False)
                # 🛡️ Suppress validation when soft-deleting
                existing._suppress_validation = True
                existing.delete()

        self.size = self.file.size
        self.filename = self.file.name

        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file and hasattr(self.file, "delete"):
            try:
                self.file.delete(save=False)  # Remove from storage
            except Exception:
                pass  # Optional: log failure

        # 🛡️ Trigger validation bypass on re-entry
        self._suppress_validation = True
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.filename} attached to {self.content_type} {self.object_id}"

    @property
    def is_profile_picture(self):
        return self.content_type.model in ["user", "company"]
