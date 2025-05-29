from app.mixins import FullyActivatedUserMixin
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, View

from .models import Notification


class NotificationListView(FullyActivatedUserMixin, ListView):
    """View for displaying all notifications for the current user."""

    template_name = "pages/notifications/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        # Get all notifications for the current user
        return self.request.user.notifications.filter(is_deleted=False).order_by(
            "-created_at"
        )


class MarkNotificationReadView(FullyActivatedUserMixin, View):
    """View for marking a notification as read."""

    def post(self, request, pk):
        notification = get_object_or_404(
            Notification, pk=pk, recipient=request.user, is_deleted=False
        )

        # Mark as read if not already read
        if not notification.read_at:
            notification.read_at = timezone.now()
            notification.save()

        # If AJAX request, return JSON response
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        # Otherwise redirect back to the notification list
        return HttpResponseRedirect(
            request.META.get("HTTP_REFERER", reverse_lazy("notifications:list"))
        )


class MarkAllNotificationsReadView(FullyActivatedUserMixin, View):
    """View for marking all notifications as read."""

    def post(self, request):
        # Get all unread notifications for the current user
        unread_notifications = request.user.notifications.filter(
            read_at__isnull=True, is_deleted=False
        )

        # Mark all as read
        now = timezone.now()
        unread_notifications.update(read_at=now)

        # If AJAX request, return JSON response
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"success": True, "count": unread_notifications.count()}
            )

        # Otherwise redirect back to the notification list with a success message
        messages.success(request, "All notifications marked as read.")
        return redirect("notifications:list")


class DeleteNotificationView(FullyActivatedUserMixin, View):
    """View for deleting a notification."""

    def post(self, request, pk):
        notification = get_object_or_404(
            Notification, pk=pk, recipient=request.user, is_deleted=False
        )

        # Soft delete the notification
        notification.delete()

        # If AJAX request, return JSON response
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        # Otherwise redirect back to the notification list with a success message
        messages.success(request, "Notification deleted.")
        return redirect("notifications:list")
