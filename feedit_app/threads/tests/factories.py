import factory
from threads.models import Thread
from accounts.tests.factories import UserFactory
from companies.tests.factories import CompanyFactory


class ThreadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Thread

    company = factory.SubFactory(CompanyFactory)
    author = factory.SubFactory(UserFactory)
    type = Thread.ThreadType.FORUM
    visibility = Thread.ThreadVisibility.INTERNAL
    title = factory.Faker("sentence")
    content = factory.Faker("paragraph")
    parent = None  # No parent by default
