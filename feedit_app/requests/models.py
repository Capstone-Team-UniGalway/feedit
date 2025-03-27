from django.conf import settings
from django.db import models
from ckeditor.fields import RichTextField
from django.contrib.auth.models import AbstractUser
# Requests made by employees to employers with status tracking
class Request(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    TYPE_CHOICES = [
        ("personal", "Personal"),
        ("medical", "Medical"),
        ("other", "Other"),
    ]
    title = models.CharField(max_length=255)
    content = RichTextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="requests_sent")
    employer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="requests_received")
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name="requests")
    created_at = models.DateTimeField(auto_now_add=True)


# Replies to private employee requests
class RequestReply(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="replies")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="request_replies")
    content = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)
