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
    tracker = FieldTracker(fields=['content'])

    def __str__(self):
        return self.title

    def get_author_name(self):
        return self.author.get_full_name() if self.author else "Unknown Author"

    def get_absolute_url(self):
        return reverse('thread_detail', kwargs={'pk': self.pk})


# Model for tracking user mentions in threads
class Mention(BaseModel):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='mentions')
    mentioned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentions_received'
    )
    mentioned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentions_created'
    )
    is_read = models.BooleanField(default=False)

    class Meta:
        unique_together = ('thread', 'mentioned_user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.mentioned_by.get_full_name()} mentioned {self.mentioned_user.get_full_name()} in {self.thread.title}"

    def mark_as_read(self):
        self.is_read = True
        self.save()


def process_mentions(sender, instance, created, **kwargs):
    """Process @mentions in thread content and create Mention objects."""
    from django.contrib.auth import get_user_model
    import re

    # Only process if this is a new thread or the content has changed
    if not created and not instance.tracker.has_changed('content'):
        return

    # Delete existing mentions for this thread
    if not created:
        instance.mentions.all().delete()

    # Extract mentions from content
    content = instance.content
    mention_pattern = r'@([a-zA-Z0-9_\s]+)'
    mentions = re.findall(mention_pattern, content)

    # Get mentioned users
    User = get_user_model()
    for mention in mentions:
        username = mention.strip()
        try:
            # Try to find the user by full name
            first_name, last_name = username.split(' ', 1)
            user = User.objects.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name
            ).first()

            if user and user != instance.author:
                # Create mention
                Mention.objects.create(
                    thread=instance,
                    mentioned_user=user,
                    mentioned_by=instance.author
                )
        except ValueError:
            # If the name doesn't have a space, try to find by first name
            user = User.objects.filter(first_name__iexact=username).first()
            if user and user != instance.author:
                # Create mention
                Mention.objects.create(
                    thread=instance,
                    mentioned_user=user,
                    mentioned_by=instance.author
                )


# Connect the signal
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Thread)
def thread_post_save(sender, instance, created, **kwargs):
    process_mentions(sender, instance, created, **kwargs)
