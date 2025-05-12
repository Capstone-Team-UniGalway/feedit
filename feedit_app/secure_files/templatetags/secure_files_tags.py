from django import template
from django.contrib.contenttypes.models import ContentType
from ..utils import get_files_for_object, get_secure_file_url

register = template.Library()


@register.simple_tag
def get_content_type_id(obj):
    """
    Get the ContentType ID for an object.

    Usage:
        {% get_content_type_id object as content_type_id %}
    """
    return ContentType.objects.get_for_model(obj.__class__).id


@register.simple_tag
def get_object_files(obj, include_deleted=False):
    """
    Get all files attached to a specific object.

    Usage:
        {% get_object_files object as files %}
    """
    return get_files_for_object(obj, include_deleted=include_deleted)


@register.simple_tag
def get_file_url(secure_file):
    """
    Get the appropriate URL for a secure file based on its content object type.

    Usage:
        {% get_file_url secure_file as file_url %}
    """
    return get_secure_file_url(secure_file)
