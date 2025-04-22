from django.conf import settings
from django.db import models
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field
from app.base_model import BaseModel
from model_utils import FieldTracker


# Group communication threads between employees and employers
class Thread(BaseModel):
    class ThreadType(models.TextChoices):
        FORUM = "forum", "Forum"  # allows replies (children)
        ANNOUNCEMENT = "announcement", "Announcement"  # no replies allowed

    class ThreadVisibility(models.TextChoices):
        INTERNAL = "internal", "Internal"  # employees & employers can read & reply
        PRIVATE = "private", "Private"  # only employees can read & reply

    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="threads"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="threads",
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )  # Self-referencing field
    type = models.CharField(
        max_length=20,
        choices=ThreadType.choices,
        default=ThreadType.FORUM,
    )
    visibility = models.CharField(
        max_length=10,
        choices=ThreadVisibility.choices,
        default=ThreadVisibility.INTERNAL,
    )
    title = models.CharField(max_length=255)
    content = CKEditor5Field()

    # Track changes to content field for mention processing
    tracker = FieldTracker(fields=["content"])

    def __str__(self):
        return self.title

    def get_author_name(self):
        return self.author.get_full_name() if self.author else "Unknown Author"

    def get_absolute_url(self):
        return reverse("thread_detail", kwargs={"pk": self.pk})


# Model for tracking user mentions in threads
class Mention(BaseModel):
    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name="mentions"
    )
    mentioned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mentions_received",
    )
    mentioned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mentions_created",
    )
    is_read = models.BooleanField(default=False)

    class Meta:
        unique_together = ("thread", "mentioned_user")
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.mentioned_by.get_full_name()} mentioned "
            f"{self.mentioned_user.get_full_name()} in {self.thread.title}"
        )

    def mark_as_read(self):
        self.is_read = True
        self.save()
