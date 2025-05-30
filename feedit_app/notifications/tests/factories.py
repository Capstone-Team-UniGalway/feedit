import factory
from accounts.tests.factories import UserFactory
from notifications.models import Notification


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    recipient = factory.SubFactory(UserFactory)
    type = Notification.NotificationType.NEW_THREAD
    message = factory.Faker("sentence")
    action_url = factory.Faker("url")
    read_at = None
