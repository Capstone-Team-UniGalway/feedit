from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string

from .models import SecureFile, get_allowed_content_types


class SecureFileForm(forms.ModelForm):
    """Form for handling secure file uploads."""

    class Meta:
        model = SecureFile
        fields = ["file"]
        widgets = {
            "file": forms.FileInput(
                attrs={"class": "file-input file-input-bordered w-full"}
            )
        }

    def __init__(self, *args, content_object=None, uploaded_by=None, **kwargs):
        self.content_object = content_object
        self.uploaded_by = uploaded_by
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        if not self.cleaned_data.get("file"):
            raise ValidationError("No file was uploaded.")

        if not self.content_object:
            raise ValidationError("Content object is required")

        # Get content type for the object
        content_type = ContentType.objects.get_for_model(self.content_object)

        # Check if content type is allowed
        if content_type.model not in get_allowed_content_types():
            raise ValidationError(
                f"Attachments to '{content_type.name}' are not allowed"
            )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set content object
        content_type = ContentType.objects.get_for_model(self.content_object)
        instance.content_type = content_type
        instance.object_id = self.content_object.id

        # Set uploaded_by if provided
        if self.uploaded_by:
            instance.uploaded_by = self.uploaded_by

        # 🔁 Dynamically assign storage backend
        if (
            settings.DEFAULT_FILE_STORAGE
            != "django.core.files.storage.FileSystemStorage"
        ):
            storage_class = import_string(settings.DEFAULT_FILE_STORAGE)
            instance.file.storage = storage_class()

        if commit:
            instance.save()

        return instance
