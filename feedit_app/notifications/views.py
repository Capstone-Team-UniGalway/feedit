from app.mixins import FullyActivatedUserMixin
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, View

from .mixins import NotificationAccessMixin


class NotificationListView(LoginRequiredMixin, ListView):
    """View for displaying all notifications for the current user."""

    template_name = "pages/notifications/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        # Get all notifications for the current user
        return self.request.user.notifications.filter(is_deleted=False).order_by(
            "-created_at"
        )


class MarkNotificationReadView(LoginRequiredMixin, NotificationAccessMixin, View):
    def post(self, request, pk):
        notification = self.get_notification(pk, request.user)

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
        unread = request.user.notifications.filter(
            read_at__isnull=True, is_deleted=False
        )

        # Mark all as read and count
        count = unread.update(read_at=timezone.now())

        # If AJAX request, return JSON response
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "count": count})

        # Otherwise redirect back to the notification list with a success message
        messages.success(request, "All notifications marked as read.")
        return redirect("notifications:list")


class DeleteNotificationView(FullyActivatedUserMixin, View):
    """View for deleting a notification."""

    def post(self, request, pk):
        notification = self.get_notification(pk, request.user)

        # Soft delete the notification
        notification.delete()

        # If AJAX request, return JSON response
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        # Otherwise redirect back to the notification list with a success message
        messages.success(request, "Notification deleted.")
        return redirect("notifications:list")
