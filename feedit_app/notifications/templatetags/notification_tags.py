from django import template
from django.utils.timesince import timesince
from notifications.models import Notification

register = template.Library()


@register.simple_tag
def unread_notifications_count(user):
    """
    Returns the count of unread notifications for a user.

    Usage:
    {% unread_notifications_count user as count %}
    """
    if not user or not user.is_authenticated:
        return 0
    return user.notifications.filter(read_at__isnull=True, is_deleted=False).count()


@register.filter
def notification_timesince(notification):
    """
    Returns a human-readable string representing how long ago the notification
    was created.

    Usage:
    {{ notification|notification_timesince }}
    """
    return timesince(notification.created_at)


@register.filter
def notification_icon(notification):
    """
    Returns the appropriate icon class for a notification type.

    Usage:
    {{ notification|notification_icon }}
    """
    icon_map = {
        Notification.NotificationType.NEW_REVIEW: "fa-star",
        Notification.NotificationType.NEW_THREAD: "fa-comment-dots",
        Notification.NotificationType.NEW_THREAD_REPLY: "fa-reply",
        Notification.NotificationType.JOIN_REQUEST: "fa-user-plus",
        Notification.NotificationType.JOIN_RESPONSE: "fa-building",
        Notification.NotificationType.CLAIM_REQUEST: "fa-flag",
        Notification.NotificationType.CLAIM_RESPONSE: "fa-check-circle",
        Notification.NotificationType.GENERAL_REQUEST: "fa-question-circle",
        Notification.NotificationType.GENERAL_RESPONSE: "fa-envelope",
    }

    return icon_map.get(notification.type, "fa-bell")


@register.filter
def notification_color(notification):
    """
    Returns the appropriate color class for a notification type.

    Usage:
    {{ notification|notification_color }}
    """
    color_map = {
        Notification.NotificationType.NEW_REVIEW: "text-warning",
        Notification.NotificationType.NEW_THREAD: "text-primary",
        Notification.NotificationType.NEW_THREAD_REPLY: "text-info",
        Notification.NotificationType.JOIN_REQUEST: "text-success",
        Notification.NotificationType.JOIN_RESPONSE: "text-success",
        Notification.NotificationType.CLAIM_REQUEST: "text-warning",
        Notification.NotificationType.CLAIM_RESPONSE: "text-warning",
        Notification.NotificationType.GENERAL_REQUEST: "text-info",
        Notification.NotificationType.GENERAL_RESPONSE: "text-info",
    }

    return color_map.get(notification.type, "text-primary")
