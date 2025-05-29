from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import Notification


class NotificationAccessMixin:
    def get_notification(self, pk, user):
        notification = get_object_or_404(Notification, pk=pk, is_deleted=False)
        if notification.recipient != user:
            raise PermissionDenied("You are not allowed to access this notification.")
        return notification
