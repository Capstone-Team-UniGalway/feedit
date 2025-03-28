from django.conf import settings
from django.db import models
from app.base_model import BaseModel


# Notification system for alerts and updates
class Notification(BaseModel):
    NOTIFICATION_TYPES = [
        ("new_review", "New Review"),
        ("new_thread", "New Thread"),
        ("new_thread_reply", "New Reply"),
        ("join_request", "New Join Request"),
        ("join_response", "New Join Response"),
        ("claim_request", "New Claim Request"),
        ("claim_request", "New Claim Response"),
        ("general_request", "New Request"),
        ("general_response", "New Response"),
    ]
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    action_url = models.URLField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)