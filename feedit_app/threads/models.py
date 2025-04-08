from django.conf import settings
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from app.base_model import BaseModel


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

    def __str__(self):
        return self.title

    def get_author_name(self):
        return self.author.get_full_name() if self.author else "Unknown Author"
