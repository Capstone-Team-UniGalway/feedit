from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from requests.models import (  # Django app name, not the Python requests library
    Request,
    RequestReply,
)

# Import models
from reviews.models import Review, ReviewReply

from .models import Notification

User = get_user_model()


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


@receiver(post_save, sender=Request)
def request_post_save(sender, instance, created, **kwargs):
    """Create a notification when a new request is created or updated."""
    # For new requests
    if created:
        if instance.type == "join" and instance.company and instance.company.employer:
            # Notify the company employer about the join request
            Notification.objects.create(
                recipient=instance.company.employer,
                type=Notification.NotificationType.JOIN_REQUEST,
                message=f"{instance.author.get_full_name()} requested to join "
                f"{instance.company.name}",
                action_url=instance.get_absolute_url(),
            )
        elif instance.type == "claim":
            # Notify superusers about the claim request
            for user in User.objects.filter(is_superuser=True, is_active=True):
                Notification.objects.create(
                    recipient=user,
                    type=Notification.NotificationType.CLAIM_REQUEST,
                    message=f"{instance.author.get_full_name()} requested to claim "
                    f"{instance.company.name}",
                    action_url=instance.get_absolute_url(),
                )
        elif (
            instance.type == "other" and instance.company and instance.company.employer
        ):
            # Notify the company employer about the general request
            Notification.objects.create(
                recipient=instance.company.employer,
                type=Notification.NotificationType.GENERAL_REQUEST,
                message=f"{instance.author.get_full_name()} submitted a request: "
                f"{instance.title}",
                action_url=instance.get_absolute_url(),
            )
    # For status updates (not new requests)
    elif (
        not created
        and kwargs.get("update_fields")
        and "status" in kwargs.get("update_fields")
    ):
        # Check if status changed to approved or rejected
        if instance.status == "approved":
            # Notify the request author about the approval
            if instance.author:
                if instance.type == "join":
                    Notification.objects.create(
                        recipient=instance.author,
                        type=Notification.NotificationType.JOIN_RESPONSE,
                        message=f"Your request to join {instance.company.name} "
                        "has been approved!",
                        action_url=instance.get_absolute_url(),
                    )
                elif instance.type == "claim":
                    Notification.objects.create(
                        recipient=instance.author,
                        type=Notification.NotificationType.CLAIM_RESPONSE,
                        message=f"Your request to claim {instance.company.name} "
                        "has been approved!",
                        action_url=instance.get_absolute_url(),
                    )
                else:
                    Notification.objects.create(
                        recipient=instance.author,
                        type=Notification.NotificationType.GENERAL_RESPONSE,
                        message=f"Your request '{instance.title}' has been approved!",
                        action_url=instance.get_absolute_url(),
                    )
        elif instance.status == "rejected":
            # Notify the request author about the rejection
            if instance.author:
                if instance.type == "join":
                    Notification.objects.create(
                        recipient=instance.author,
                        type=Notification.NotificationType.JOIN_RESPONSE,
                        message=f"Your request to join {instance.company.name} "
                        "has been rejected.",
                        action_url=instance.get_absolute_url(),
                    )
                elif instance.type == "claim":
                    Notification.objects.create(
                        recipient=instance.author,
                        type=Notification.NotificationType.CLAIM_RESPONSE,
                        message=f"Your request to claim {instance.company.name} "
                        "has been rejected.",
                        action_url=instance.get_absolute_url(),
                    )
                else:
                    Notification.objects.create(
                        recipient=instance.author,
                        type=Notification.NotificationType.GENERAL_RESPONSE,
                        message=f"Your request '{instance.title}' has been rejected.",
                        action_url=instance.get_absolute_url(),
                    )


@receiver(post_save, sender=RequestReply)
def request_reply_post_save(sender, instance, created, **kwargs):
    """Create a notification when a request reply is created."""
    if created:
        # Determine the recipient (the other party in the conversation)
        request_obj = instance.request
        recipient = (
            request_obj.author
            if instance.author != request_obj.author
            else request_obj.company.employer
        )

        if recipient:
            # Determine notification type based on request type
            if request_obj.type == "join":
                notification_type = Notification.NotificationType.JOIN_RESPONSE
            elif request_obj.type == "claim":
                notification_type = Notification.NotificationType.CLAIM_RESPONSE
            else:
                notification_type = Notification.NotificationType.GENERAL_RESPONSE

            # Create the notification
            Notification.objects.create(
                recipient=recipient,
                type=notification_type,
                message=f"{instance.author.get_full_name()} replied to your request: "
                f"{request_obj.title}",
                action_url=request_obj.get_absolute_url(),
            )
