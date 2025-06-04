import factory
from companies.models import Company
from accounts.tests.factories import UserFactory
import datetime


class CompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Company

    name = factory.Sequence(lambda n: f"Test Company {n}")
    industry = "Technology"
    bio = factory.Faker("paragraph")
    country = "Ireland"
    city = "Galway"
    employer = factory.SubFactory(UserFactory)
    date_founded = datetime.date(2000, 1, 1)
