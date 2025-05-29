from app.base_model import BaseModel
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field


# Requests made by employees to employers with status tracking
class Request(BaseModel):
    class RequestType(models.TextChoices):
        JOIN = "join", "Join"
        CLAIM = "claim", "Claim"
        OTHER = "other", "Other"

    class RequestStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

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
    type = models.CharField(max_length=10, choices=RequestType.choices)
    status = models.CharField(
        max_length=10, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )
    title = models.CharField(max_length=255)
    content = CKEditor5Field()

    def __str__(self):
        return f"{self.get_type_display()} Request: {self.title}"

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("requests:detail", kwargs={"pk": self.pk})

    def can_be_processed_by(self, user):
        if not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        if self.type in [
            Request.RequestType.JOIN,
            Request.RequestType.OTHER,
        ]:
            return self.company and self.company.employer == user

        # optionally extend to other types if needed
        return False


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

    attachments = GenericRelation(
        "secure_files.SecureFile",
        content_type_field="content_type",
        object_id_field="object_id",
        related_query_name="requestreply_attachments",
    )

    class Meta:
        verbose_name = "Request Reply"
        verbose_name_plural = "Request Replies"
