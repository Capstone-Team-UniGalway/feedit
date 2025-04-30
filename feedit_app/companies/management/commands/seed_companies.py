import random
from django.core.management.base import BaseCommand
from companies.tests.factories import CompanyFactory
from accounts.tests.factories import UserFactory

COUNTRIES = [
    "Ireland",
    "Germany",
    "France",
    "Canada",
    "United States",
    "Sweden",
    "Japan",
    "Australia",
    "Netherlands",
    "Brazil",
]

INDUSTRIES = [
    "Technology",
    "Healthcare",
    "Finance",
    "Education",
    "Manufacturing",
    "Retail",
    "Transportation",
    "Hospitality",
    "Energy",
    "Telecommunications",
]


class Command(BaseCommand):
    help = "Seed demo companies and employers"

    def handle(self, *args, **kwargs):
        for _ in range(10):
            employer = UserFactory(type="employer")
            CompanyFactory(
                employer=employer,
                country=random.choice(COUNTRIES),
                industry=random.choice(INDUSTRIES),
            )
        self.stdout.write(self.style.SUCCESS("Seeded 10 companies with employers"))
