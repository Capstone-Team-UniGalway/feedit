# Connect the signal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.urls import reverse
from .models import Thread, Mention
from django.contrib.auth import get_user_model
import re

# Import the Notification model if it exists
try:
    from notifications.models import Notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False


@receiver(post_save, sender=Thread)
def thread_post_save(sender, instance, created, **kwargs):
    process_mentions(sender, instance, created, **kwargs)


@receiver(post_save, sender=Mention)
def mention_post_save(sender, instance, created, **kwargs):
    """Create a notification when a user is mentioned."""
    if created and NOTIFICATIONS_AVAILABLE:
        thread = instance.thread
        mentioned_user = instance.mentioned_user
        author = thread.author

        if author and mentioned_user:
            # Create notification
            Notification.objects.create(
                recipient=mentioned_user,
                type=Notification.NotificationType.NEW_THREAD if thread.parent is None else Notification.NotificationType.NEW_THREAD_REPLY,
                message=f"{author.get_full_name()} mentioned you in '{thread.title}'",
                action_url=reverse('thread_detail', kwargs={'pk': thread.pk})
            )


def process_mentions(sender, instance, created, **kwargs):
    """Process @mentions in thread content and create Mention objects."""

    # Always process mentions for new threads
    # For existing threads, only process if content has changed
    if not created and not instance.tracker.has_changed("content"):
        print(f"Skipping mention processing for thread {instance.id} - content unchanged")
        return

    print(f"Processing mentions for thread {instance.id} - {'new thread' if created else 'content changed'}")

    # Delete existing mentions for this thread
    if not created:
        instance.mentions.all().delete()

    # Extract mentions from content
    content = instance.content
    print(f"Thread content: {content[:100]}...")  # Print first 100 chars for debugging

    # Look for all mention formats:
    # 1. New format: @Username[123] with embedded user ID
    # 2. Legacy format: @Username without ID
    # 3. HTML links with data-mention attribute (from rendered content)
    # 4. HTML links with class="mention" (from rendered content)
    # 5. Simple @username format (most common)

    # Match @Username[123] format
    new_mention_pattern = r"@([a-zA-Z0-9_\s]+)\[(\d+)\]"

    # Match simple @username format (without brackets)
    legacy_mention_pattern = r"@([a-zA-Z0-9_\s]+)(?!\[\d+\])"

    # Match mentions with HTML tags like "@Emp Two/a>"
    legacy_html_mention_pattern = r"@([a-zA-Z0-9_\s]+)(?:</a>|</span>)"

    # Match HTML mentions with data-mention-id attribute
    html_mention_pattern = r'data-mention-id="(\d+)"[^>]*>@([^<]+)<'

    # Match HTML mentions with class="mention"
    html_class_mention_pattern = r'class="mention"[^>]*data-mention-id="(\d+)"[^>]*>@([^<]+)<'

    new_mentions = re.findall(new_mention_pattern, content)
    legacy_mentions = re.findall(legacy_mention_pattern, content)
    legacy_html_mentions = re.findall(legacy_html_mention_pattern, content)
    html_mentions = re.findall(html_mention_pattern, content)
    html_class_mentions = re.findall(html_class_mention_pattern, content)

    print(f"Found mentions - New format: {len(new_mentions)}, Legacy format: {len(legacy_mentions)}, Legacy HTML: {len(legacy_html_mentions)}, HTML: {len(html_mentions)}, HTML class: {len(html_class_mentions)}")
    if new_mentions:
        print(f"New format mentions: {new_mentions}")
    if legacy_mentions:
        print(f"Legacy format mentions: {legacy_mentions}")
    if legacy_html_mentions:
        print(f"Legacy HTML mentions: {legacy_html_mentions}")
    if html_mentions:
        print(f"HTML mentions: {html_mentions}")
    if html_class_mentions:
        print(f"HTML class mentions: {html_class_mentions}")

    # Process mentions in order of reliability
    User = get_user_model()
    processed_user_ids = set()

    # 1. First process new format mentions (most reliable as they have embedded IDs)
    for username, user_id_str in new_mentions:
        try:
            user_id = int(user_id_str)
            user = User.objects.filter(id=user_id, is_active=True).first()

            if user and user.id not in processed_user_ids:  # Allow self-mentions
                # Create mention
                mention = Mention.objects.create(thread=instance, mentioned_user=user)
                processed_user_ids.add(user.id)
                print(f"Created mention (new format): {user.get_full_name()} (ID: {mention.id})")
        except (ValueError, TypeError):
            # Skip invalid user IDs
            continue

    # 2. Process HTML mentions (also reliable as they have explicit IDs)
    for user_id_str, username in html_mentions:
        try:
            user_id = int(user_id_str)
            # Skip if already processed
            if user_id in processed_user_ids:
                continue

            user = User.objects.filter(id=user_id, is_active=True).first()

            if user and user.id not in processed_user_ids:  # Allow self-mentions
                # Create mention
                mention = Mention.objects.create(thread=instance, mentioned_user=user)
                processed_user_ids.add(user.id)
                print(f"Created mention (HTML format): {user.get_full_name()} (ID: {mention.id})")
        except (ValueError, TypeError):
            # Skip invalid user IDs
            continue

    # 3. Process HTML class mentions (also reliable as they have explicit IDs)
    for user_id_str, username in html_class_mentions:
        try:
            user_id = int(user_id_str)
            # Skip if already processed
            if user_id in processed_user_ids:
                continue

            user = User.objects.filter(id=user_id, is_active=True).first()

            if user and user.id not in processed_user_ids:  # Allow self-mentions
                # Create mention
                mention = Mention.objects.create(thread=instance, mentioned_user=user)
                processed_user_ids.add(user.id)
                print(f"Created mention (HTML class format): {user.get_full_name()} (ID: {mention.id})")
        except (ValueError, TypeError):
            # Skip invalid user IDs
            continue

    # Get the company for legacy mention processing
    company = None
    if instance.author:
        if hasattr(instance.author, "workplace") and instance.author.workplace:
            company = instance.author.workplace
        elif hasattr(instance.author, "company"):
            company = instance.author.company

    # 4. Process legacy HTML mentions (with HTML tags)
    if company:
        for username in legacy_html_mentions:
            username = username.strip()

            # Skip if already processed via other mention formats
            if any(username == html_username for _, html_username in html_mentions):
                continue

            if any(username == new_username for new_username, _ in new_mentions):
                continue

            try:
                # Try to find the user by full name
                if " " in username:
                    first_name, last_name = username.split(" ", 1)
                    user = User.objects.filter(
                        first_name__iexact=first_name,
                        last_name__iexact=last_name,
                        is_active=True
                    ).filter(
                        models.Q(workplace=company) | models.Q(company=company)
                    ).first()
                else:
                    # If no space, try by first name but only within company
                    user = User.objects.filter(
                        first_name__iexact=username,
                        is_active=True
                    ).filter(
                        models.Q(workplace=company) | models.Q(company=company)
                    ).first()

                if user and user.id not in processed_user_ids:  # Allow self-mentions
                    # Create mention
                    mention = Mention.objects.create(thread=instance, mentioned_user=user)
                    processed_user_ids.add(user.id)
                    print(f"Created mention (legacy HTML format): {user.get_full_name()} (ID: {mention.id})")
            except Exception as e:
                # Skip any errors in mention processing
                print(f"Error processing legacy HTML mention: {e}")
                continue

    # 5. Process legacy text mentions (least reliable, requires name lookup)
    # Only process users from the same company for security
    if company:
        for username in legacy_mentions:
            username = username.strip()

            # Skip if already processed via other mention formats
            if any(username == html_username for _, html_username in html_mentions):
                continue

            if any(username == new_username for new_username, _ in new_mentions):
                continue

            try:
                # Try to find the user by full name
                if " " in username:
                    first_name, last_name = username.split(" ", 1)
                    user = User.objects.filter(
                        first_name__iexact=first_name,
                        last_name__iexact=last_name,
                        is_active=True
                    ).filter(
                        models.Q(workplace=company) | models.Q(company=company)
                    ).first()
                else:
                    # If no space, try by first name but only within company
                    user = User.objects.filter(
                        first_name__iexact=username,
                        is_active=True
                    ).filter(
                        models.Q(workplace=company) | models.Q(company=company)
                    ).first()

                if user and user.id not in processed_user_ids:  # Allow self-mentions
                    # Create mention
                    mention = Mention.objects.create(thread=instance, mentioned_user=user)
                    processed_user_ids.add(user.id)
                    print(f"Created mention (legacy format): {user.get_full_name()} (ID: {mention.id})")
            except Exception as e:
                # Skip any errors in mention processing
                print(f"Error processing legacy mention: {e}")
                continue

    # Note: We've removed the redundant "simple mentions" processing section
    # as it was duplicating the functionality of the legacy mentions section
