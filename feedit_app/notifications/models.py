from django.conf import settings
from django.db import models
from app.base_model import BaseModel


# Notification system for alerts and updates
class Notification(BaseModel):

    class NotificationType(models.TextChoices):
        NEW_REVIEW = "new_review", "New Review"
        NEW_THREAD = "new_thread", "New Thread"
        NEW_THREAD_REPLY = "new_thread_reply", "New Reply"
        JOIN_REQUEST = "join_request", "New Join Request"
        JOIN_RESPONSE = "join_response", "New Join Response"
        CLAIM_REQUEST = "claim_request", "New Claim Request"
        CLAIM_RESPONSE = "claim_response", "New Claim Response"
        GENERAL_REQUEST = "general_request", "New Request"
        GENERAL_RESPONSE = "general_response", "New Response"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
    )
    message = models.TextField()
    action_url = models.URLField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
