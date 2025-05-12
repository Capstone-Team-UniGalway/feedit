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

    queryset = SecureFile.objects.filter(
        content_type=content_type,
        object_id=obj.id
    )

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
    Get the appropriate URL for a secure file based on its content object type.

    Args:
        secure_file: The SecureFile instance

    Returns:
        URL string for accessing the file with proper permissions
    """
    # Get the content object
    content_object = secure_file.content_object

    # Check if content object is a Request
    if content_object and hasattr(content_object, 'type'):
        # Import Request model to check request types
        from django.apps import apps
        Request = apps.get_model('requests', 'Request')

        # Check if content object is a Request
        if isinstance(content_object, Request):
            # Check request type
            if content_object.type == Request.RequestType.JOIN:
                # Join request file
                return reverse('secure_files:download_join_request_file', kwargs={
                    'join_request_id': content_object.id,
                    'secure_file_id': secure_file.id
                })
            elif content_object.type == Request.RequestType.CLAIM:
                # Claim request file
                return reverse('secure_files:download_claim_request_file', kwargs={
                    'claim_request_id': content_object.id,
                    'secure_file_id': secure_file.id
                })

    # Default to standard secure file download URL
    return reverse('secure_files:download', kwargs={'file_id': secure_file.id})
