#!/usr/bin/env python
"""
Test script to verify that mentions notifications are working correctly.
This script tests the fix for the mentions notification system.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from django.contrib.auth import get_user_model
from threads.models import Thread, Mention
from notifications.models import Notification
from companies.models import Company

User = get_user_model()

import pytest

@pytest.mark.django_db
def test_mentions_notifications():
    """Test that mentions in threads create notifications."""

    print("=== Testing Mentions Notification System ===\n")

    # Get current counts
    initial_mentions = Mention.objects.count()
    initial_notifications = Notification.objects.count()

    print(f"Initial state:")
    print(f"  Mentions: {initial_mentions}")
    print(f"  Notifications: {initial_notifications}")

    # Get or create test users
    try:
        author = User.objects.filter(is_active=True, type=User.UserType.EMPLOYEE).first()
        mentioned_user = User.objects.filter(is_active=True, type=User.UserType.EMPLOYEE).exclude(id=author.id if author else None).first()

        if not author or not mentioned_user:
            print("❌ Error: Need at least 2 active employee users to test mentions")
            return False

        print(f"\nTest users:")
        print(f"  Author: {author.get_full_name()} (ID: {author.id})")
        print(f"  Mentioned: {mentioned_user.get_full_name()} (ID: {mentioned_user.id})")

        # Get a company for the thread
        company = author.workplace or Company.objects.first()
        if not company:
            print("❌ Error: No company available for thread creation")
            return False

        print(f"  Company: {company.name}")

        # Create a thread with a mention using the new format @Username[ID]
        mention_text = f"@{mentioned_user.get_full_name()}[{mentioned_user.id}]"
        thread_content = f"<p>Hello {mention_text}, please check this out!</p>"

        print(f"\nCreating thread with mention: {mention_text}")

        # Create the thread
        thread = Thread.objects.create(
            company=company,
            author=author,
            title="Test Thread with Mention",
            content=thread_content,
            type=Thread.ThreadType.FORUM,
            visibility=Thread.ThreadVisibility.INTERNAL
        )

        print(f"✅ Thread created: {thread.title} (ID: {thread.id})")

        # Check if mention was created
        new_mentions = Mention.objects.count()
        new_notifications = Notification.objects.count()

        print(f"\nAfter thread creation:")
        print(f"  Mentions: {new_mentions} (change: +{new_mentions - initial_mentions})")
        print(f"  Notifications: {new_notifications} (change: +{new_notifications - initial_notifications})")

        # Check specific mention
        mention = Mention.objects.filter(thread=thread, mentioned_user=mentioned_user).first()
        if mention:
            print(f"✅ Mention created: {mention}")
        else:
            print("❌ No mention found for the mentioned user")
            return False

        # Check specific notification
        notification = Notification.objects.filter(
            recipient=mentioned_user,
            type=Notification.NotificationType.NEW_THREAD
        ).order_by('-created_at').first()

        if notification:
            print(f"✅ Notification created: {notification.message}")
            print(f"   Type: {notification.type}")
            print(f"   Action URL: {notification.action_url}")
        else:
            print("❌ No notification found for the mentioned user")
            return False

        print("\n🎉 Mentions notification system is working correctly!")
        return True

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mentions_notifications()
    sys.exit(0 if success else 1)
