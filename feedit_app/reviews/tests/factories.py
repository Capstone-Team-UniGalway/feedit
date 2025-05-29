import factory
from accounts.tests.factories import UserFactory
from companies.tests.factories import CompanyFactory
from reviews.models import Review, ReviewReply


class ReviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Review

    company = factory.SubFactory(CompanyFactory)
    user = factory.SubFactory(UserFactory)
    rating = 4.5
    content = factory.Faker("paragraph")
    is_anonymous = False
    guest_name = None


class ReviewReplyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReviewReply

    review = factory.SubFactory(ReviewFactory)
    employer = factory.SubFactory(UserFactory)
    content = factory.Faker("paragraph")
