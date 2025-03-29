from django.conf import settings
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from app.base_model import BaseModel


# Requests made by employees to employers with status tracking
class Request(BaseModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    TYPE_CHOICES = [
        ("join", "Join"),
        ("claim", "Claim"),
        ("other", "Other"),
    ]
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requests_sent",
    )
    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="requests"
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    title = models.CharField(max_length=255)
    content = CKEditor5Field()


# Replies to private employee requests
class RequestReply(BaseModel):
    request = models.ForeignKey(
        Request, on_delete=models.CASCADE, related_name="replies"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="request_replies",
    )
    content = CKEditor5Field()

    class Meta:
        verbose_name = "Request Reply"
        verbose_name_plural = "Request Replies"
