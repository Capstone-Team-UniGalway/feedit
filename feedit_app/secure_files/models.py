from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from app.base_model import BaseModel

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_CONTENT_TYPES = ["user", "company", "thread", "request", "request_reply"]
IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]


def validate_file_size(file):
    if file.size > MAX_FILE_SIZE:
        raise ValidationError("Max file size is 10MB.")


def upload_to(instance, filename):
    return f"attachments/{instance.content_type.model}/{filename}"


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
        model = self.content_type.model

        # ✅ Enforce allowed content types
        if model not in ALLOWED_CONTENT_TYPES:
            raise ValidationError(
                f"Attachments to '{self.content_type.name}' are not allowed."
            )

        # ✅ Only allow image files except for request/request_reply
        extension = self.file.name.split(".")[-1].lower()
        if (
            model not in ["request", "request_reply"]
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
                existing.delete()

        if self.file:
            self.size = self.file.size
            self.filename = self.file.name

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.filename} attached to {self.content_type} {self.object_id}"

    @property
    def is_profile_picture(self):
        return self.content_type.model in ["user", "company"]
