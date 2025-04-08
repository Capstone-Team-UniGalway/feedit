from django.conf import settings
from django.db import models
from app.base_model import BaseModel
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


def validate_rating_step(value):
    """Custom validator to enforce step size of 0.5"""
    if (value * 10) % 5 != 0:  # Ensures values like 0.5, 1.0, 1.5, ..., 5.0
        raise ValidationError("Rating must be in 0.5 increments.")


# Anonymous or named reviews about companies
class Review(BaseModel):
    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="reviews"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
    )
    guest_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Required if no user is associated and not anonymous",
    )
    rating = models.FloatField(
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(5.0),
            validate_rating_step,
        ]
    )
    content = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Ensure guest name is provided when no user and not anonymous
        if not self.user and not self.is_anonymous and not self.guest_name:
            raise ValidationError("Guest name is required if not anonymous.")

    def __str__(self):
        if self.is_anonymous:
            name = "Anonymous"
        elif self.user:
            name = self.user
        elif self.guest_name:
            name = self.guest_name
        else:
            return f"Review - {self.rating}/5"

        return f"Review by {name} - {self.rating}/5"


# Employer replies to reviews
class ReviewReply(BaseModel):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="replies")
    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="review_replies",
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Review Reply"
        verbose_name_plural = "Review Replies"
