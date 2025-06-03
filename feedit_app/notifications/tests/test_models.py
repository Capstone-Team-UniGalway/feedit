import pytest
from notifications.models import Notification
from .factories import NotificationFactory
from django.utils import timezone

pytestmark = pytest.mark.django_db


def test_notification_factory_creates_valid_instance():
    note = NotificationFactory()
    assert isinstance(note, Notification)
    assert note.type == Notification.NotificationType.NEW_THREAD
    assert note.recipient is not None
    assert note.read_at is None


def test_notification_str_fields():
    note = NotificationFactory(message="You got a reply")
    assert "reply" in note.message


def test_notification_can_be_marked_as_read():
    note = NotificationFactory(read_at=None)
    assert note.read_at is None

    note.read_at = timezone.now()
    note.save()

    refreshed = Notification.objects.get(pk=note.pk)
    assert refreshed.read_at is not None


def test_notification_type_choices_are_valid():
    for t in Notification.NotificationType.values:
        note = NotificationFactory(type=t)
        assert note.type == t
