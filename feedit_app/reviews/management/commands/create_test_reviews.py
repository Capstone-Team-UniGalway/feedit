import random
from datetime import datetime, timedelta

from companies.models import Company
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from reviews.models import Review, ReviewReply

User = get_user_model()


class Command(BaseCommand):
    help = "Create test reviews for demonstration purposes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--company-id",
            type=int,
            default=1,
            help="Company ID to create reviews for (default: 1)",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=5,
            help="Number of reviews to create (default: 5)",
        )

    def handle(self, *args, **options):
        company_id = options["company_id"]
        count = options["count"]

        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Company with ID {company_id} does not exist")
            )
            return

        # Sample review data
        sample_reviews = [
            {
                "rating": 4.5,
                "content": (
                    "Great company to work for! The management is supportive "
                    "and the work environment is collaborative. Really enjoying "
                    "my time here."
                ),
                "guest_name": "Sarah Johnson",
                "is_anonymous": False,
            },
            {
                "rating": 5.0,
                "content": (
                    "Excellent workplace culture and amazing benefits. "
                    "The team is very welcoming and there are great "
                    "opportunities for growth."
                ),
                "guest_name": "Michael Chen",
                "is_anonymous": False,
            },
            {
                "rating": 3.5,
                "content": (
                    "Decent place to work. Good work-life balance but could "
                    "improve on communication between departments."
                ),
                "guest_name": None,
                "is_anonymous": True,
            },
            {
                "rating": 4.0,
                "content": (
                    "Professional environment with good learning opportunities. "
                    "Management is approachable and the projects are interesting."
                ),
                "guest_name": "Emily Rodriguez",
                "is_anonymous": False,
            },
            {
                "rating": 2.5,
                "content": (
                    "The work is okay but there are some organizational issues "
                    "that need to be addressed. Hope things improve."
                ),
                "guest_name": None,
                "is_anonymous": True,
            },
            {
                "rating": 4.5,
                "content": (
                    "Really positive experience working here. Great team dynamics "
                    "and the company values align with my personal values."
                ),
                "guest_name": "David Kim",
                "is_anonymous": False,
            },
            {
                "rating": 3.0,
                "content": (
                    "Average workplace. Some good aspects but also room for "
                    "improvement in terms of career development opportunities."
                ),
                "guest_name": "Jennifer Smith",
                "is_anonymous": False,
            },
        ]

        created_reviews = []

        for i in range(min(count, len(sample_reviews))):
            review_data = sample_reviews[i]

            # Create review with a random date in the past 30 days
            days_ago = random.randint(1, 30)
            created_at = datetime.now() - timedelta(days=days_ago)

            review = Review.objects.create(
                company=company,
                user=None,  # Guest reviews
                guest_name=review_data["guest_name"],
                rating=review_data["rating"],
                content=review_data["content"],
                is_anonymous=review_data["is_anonymous"],
            )

            # Manually set the created_at date
            review.created_at = created_at
            review.save()

            created_reviews.append(review)

            # Randomly add replies to some reviews (30% chance)
            if random.random() < 0.3 and company.employer:
                reply_content = [
                    "Thank you for your feedback! "
                    "We're glad you're enjoying your time with us.",
                    "We appreciate your review and will continue "
                    "working to improve our workplace.",
                    "Thanks for the honest feedback. "
                    "We're always looking for ways to enhance our team's experience.",
                    "We value your input and are committed to "
                    "making this a great place to work.",
                ][random.randint(0, 3)]

                ReviewReply.objects.create(
                    review=review,
                    employer=company.employer,
                    content=reply_content,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(created_reviews)} "
                f"test reviews for {company.name}"
            )
        )

        # Show summary
        total_reviews = company.reviews.count()
        avg_rating = (
            sum(r.rating for r in company.reviews.all()) / total_reviews
            if total_reviews > 0
            else 0
        )

        self.stdout.write(f"Company now has {total_reviews} total reviews")
        self.stdout.write(f"Average rating: {avg_rating:.1f}/5.0")
