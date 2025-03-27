from django.conf import settings
from django.db import models
from ckeditor.fields import RichTextField
from django.contrib.auth.models import AbstractUser
# Notification system for alerts and updates
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("review_alert", "Review Alert"),
        ("thread_alert", "Thread Alert"),
        ("employee_alert", "New Employee Alert"),
        ("claim_alert", "Claim/Join Alert"),
    ]
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)