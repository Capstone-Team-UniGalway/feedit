import factory
from requests.models import Request, RequestReply
from accounts.tests.factories import UserFactory
from companies.tests.factories import CompanyFactory


class RequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Request

    author = factory.SubFactory(UserFactory)
    company = factory.SubFactory(CompanyFactory)
    type = Request.RequestType.JOIN
    status = Request.RequestStatus.PENDING
    title = factory.Faker("sentence")
    content = factory.Faker("paragraph")


class RequestReplyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RequestReply

    request = factory.SubFactory(RequestFactory)
    author = factory.SubFactory(UserFactory)
    content = factory.Faker("paragraph")
