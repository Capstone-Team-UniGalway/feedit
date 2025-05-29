from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from .models import SecureFile


def get_files_for_object(obj, include_deleted=False):
    """
    Get all files attached to a specific object.

    Args:
        obj: The object to get files for
        include_deleted: Whether to include deleted files

    Returns:
        QuerySet of SecureFile objects
    """
    content_type = ContentType.objects.get_for_model(obj)

    queryset = SecureFile.objects.filter(content_type=content_type, object_id=obj.id)

    if not include_deleted:
        queryset = queryset.filter(is_deleted=False)

    return queryset


def get_content_type_for_model(model_class):
    """
    Get the ContentType for a model class.

    Args:
        model_class: The model class to get the ContentType for

    Returns:
        ContentType instance
    """
    return ContentType.objects.get_for_model(model_class)


def get_secure_file_url(secure_file):
    """
    Returns the unified secure download URL for a SecureFile instance.
    All access control is handled in the view.

    Args:
        secure_file: The SecureFile instance

    Returns:
        URL string for accessing the file with proper permissions
    """
    return reverse("secure_files:download", kwargs={"file_id": secure_file.id})
