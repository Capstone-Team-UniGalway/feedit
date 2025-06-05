from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from notifications.models import Notification

from .models import Review, ReviewReply


@receiver(post_save, sender=Review)
def review_post_save(sender, instance, created, **kwargs):
    """Create a notification when a new review is created."""
    if created and instance.company and instance.company.employer:
        # Make sure the reviewer is not the employer
        if instance.user != instance.company.employer:
            # Get the reviewer's name
            if instance.is_anonymous:
                reviewer_name = "Anonymous"
            elif instance.user:
                reviewer_name = instance.user.get_full_name()
            elif instance.guest_name:
                reviewer_name = instance.guest_name
            else:
                reviewer_name = "Unknown"

            # Notify the company employer about the new review
            Notification.objects.create(
                recipient=instance.company.employer,
                type=Notification.NotificationType.NEW_REVIEW,
                message=f"New review by {reviewer_name} for {instance.company.name}: "
                f"{instance.rating}/5",
                action_url=reverse(
                    "companies:detail", kwargs={"pk": instance.company.pk}
                ),
            )


@receiver(post_save, sender=ReviewReply)
def review_reply_post_save(sender, instance, created, **kwargs):
    """Create a notification when a review reply is created."""
    if created and instance.review.user:
        # Notify the review author about the employer's reply
        Notification.objects.create(
            recipient=instance.review.user,
            type=Notification.NotificationType.NEW_REVIEW,
            message=f"{instance.employer.get_full_name()} replied to your review of "
            f"{instance.review.company.name}",
            action_url=reverse(
                "companies:detail", kwargs={"pk": instance.review.company.pk}
            ),
        )
