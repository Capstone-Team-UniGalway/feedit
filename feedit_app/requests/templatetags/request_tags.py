from django import template
from requests.models import Request

register = template.Library()


@register.filter
def get_type_badge_color(request_type):
    """Returns the appropriate badge color for a request type."""
    colors = {
        Request.RequestType.JOIN: "primary",
        Request.RequestType.CLAIM: "secondary",
        Request.RequestType.OTHER: "accent",
    }
    return colors.get(request_type, "neutral")


@register.filter
def get_status_badge_color(status):
    """Returns the appropriate badge color for a request status."""
    colors = {
        Request.RequestStatus.PENDING: "warning",
        Request.RequestStatus.APPROVED: "success",
        Request.RequestStatus.REJECTED: "error",
    }
    return colors.get(status, "neutral")
