import re
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from .models import Mention, Thread

# Optional Notification integration
try:
    from notifications.models import Notification

    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False


@receiver(post_save, sender=Thread)
def thread_post_save(sender, instance, created, **kwargs):
    process_mentions(instance, created)


@receiver(post_save, sender=Mention)
def mention_post_save(sender, instance, created, **kwargs):
    """Create a notification when a user is mentioned."""
    if created and NOTIFICATIONS_AVAILABLE:
        thread = instance.thread
        mentioned_user = instance.mentioned_user
        author = thread.author

        if author and mentioned_user:
            Notification.objects.create(
                recipient=mentioned_user,
                type=(
                    Notification.NotificationType.NEW_THREAD
                    if thread.parent is None
                    else Notification.NotificationType.NEW_THREAD_REPLY
                ),
                message=f"{author.get_full_name()} mentioned you in '{thread.title}'",
                action_url=reverse("thread_detail", kwargs={"pk": thread.pk}),
            )


def process_mentions(instance, created):
    """
    Extract mentions in the format @Full Name [user_id]
    and create Mention objects.
    """
    if not created and not instance.tracker.has_changed("content"):
        return

    content = instance.content
    pattern = r"@([A-Za-z0-9_\s]+)\s\[(\d+)\]"  # Match @Name [ID]
    matches = re.findall(pattern, content)

    User = get_user_model()
    author = instance.author
    company = getattr(author, "workplace", None) or getattr(author, "company", None)
    if not company:
        return

    if not created:
        instance.mentions.all().delete()

    processed_user_ids = set()

    for full_name, user_id_str in matches:
        try:
            user_id = int(user_id_str)
            if user_id in processed_user_ids:
                continue

            user = (
                User.objects.filter(id=user_id, is_active=True)
                .filter(models.Q(workplace=company) | models.Q(company=company))
                .first()
            )
            if user:
                Mention.objects.create(thread=instance, mentioned_user=user)
                processed_user_ids.add(user.id)

        except Exception as e:
            print(f"Error processing mention for '{full_name} [{user_id_str}]': {e}")
            continue
