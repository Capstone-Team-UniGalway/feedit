# Connect the signal
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Thread, Mention
from django.contrib.auth import get_user_model
import re


@receiver(post_save, sender=Thread)
def thread_post_save(sender, instance, created, **kwargs):
    process_mentions(sender, instance, created, **kwargs)


def process_mentions(sender, instance, created, **kwargs):
    """Process @mentions in thread content and create Mention objects."""

    # Only process if this is a new thread or the content has changed
    if not created and not instance.tracker.has_changed("content"):
        return

    # Delete existing mentions for this thread
    if not created:
        instance.mentions.all().delete()

    # Extract mentions from content
    content = instance.content
    mention_pattern = r"@([a-zA-Z0-9_\s]+)"
    mentions = re.findall(mention_pattern, content)

    # Get mentioned users
    User = get_user_model()
    for mention in mentions:
        username = mention.strip()
        try:
            # Try to find the user by full name
            first_name, last_name = username.split(" ", 1)
            user = User.objects.filter(
                first_name__iexact=first_name, last_name__iexact=last_name
            ).first()

            if user and user != instance.author:
                # Create mention
                Mention.objects.create(
                    thread=instance, mentioned_user=user, mentioned_by=instance.author
                )
        except ValueError:
            # If the name doesn't have a space, try to find by first name
            user = User.objects.filter(first_name__iexact=username).first()
            if user and user != instance.author:
                # Create mention
                Mention.objects.create(
                    thread=instance, mentioned_user=user, mentioned_by=instance.author
                )
