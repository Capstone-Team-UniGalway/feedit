from .models import (
    Request,
    RequestReply,
)
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.models import Notification

User = get_user_model()


def send_request_notification(recipient, request_obj, notif_type, message):
    if recipient:
        Notification.objects.create(
            recipient=recipient,
            type=notif_type,
            message=message,
            action_url=request_obj.get_absolute_url(),
        )


@receiver(post_save, sender=Request)
def request_post_save(sender, instance, created, **kwargs):
    """Create a notification when a new request is created or updated."""
    # For new requests
    if created:
        author_name = instance.author.get_full_name() if instance.author else "Someone"

        if instance.type == "join" and instance.company and instance.company.employer:
            send_request_notification(
                recipient=instance.company.employer,
                request_obj=instance,
                notif_type=Notification.NotificationType.JOIN_REQUEST,
                message=f"{author_name} requested to join {instance.company.name}",
            )
        elif instance.type == "claim":
            # Notify superusers about the claim request
            for superuser in User.objects.filter(is_superuser=True, is_active=True):
                send_request_notification(
                    recipient=superuser,
                    request_obj=instance,
                    notif_type=Notification.NotificationType.CLAIM_REQUEST,
                    message=f"{author_name} requested to claim {instance.company.name}",
                )
        elif (
            instance.type == "other" and instance.company and instance.company.employer
        ):
            # Notify the company employer about the general request
            send_request_notification(
                recipient=instance.company.employer,
                request_obj=instance,
                notif_type=Notification.NotificationType.GENERAL_REQUEST,
                message=f"{author_name} submitted a request: {instance.title}",
            )
    # For status updates (not new requests)
    elif (
        not created
        and kwargs.get("update_fields")
        and "status" in kwargs.get("update_fields")
    ):
        status = instance.status
        company_name = instance.company.name
        title = instance.title
        recipient = instance.author

        notif_map = {
            ("join", "approved"): (
                Notification.NotificationType.JOIN_RESPONSE,
                f"Your request to join {company_name} has been approved!",
            ),
            ("join", "rejected"): (
                Notification.NotificationType.JOIN_RESPONSE,
                f"Your request to join {company_name} has been rejected.",
            ),
            ("claim", "approved"): (
                Notification.NotificationType.CLAIM_RESPONSE,
                f"Your request to claim {company_name} has been approved!",
            ),
            ("claim", "rejected"): (
                Notification.NotificationType.CLAIM_RESPONSE,
                f"Your request to claim {company_name} has been rejected.",
            ),
            ("other", "approved"): (
                Notification.NotificationType.GENERAL_RESPONSE,
                f"Your request '{title}' has been approved!",
            ),
            ("other", "rejected"): (
                Notification.NotificationType.GENERAL_RESPONSE,
                f"Your request '{title}' has been rejected.",
            ),
        }

        notif_type, message = notif_map.get((instance.type, status), (None, None))
        if notif_type:
            # Notify the request author about the new status
            send_request_notification(recipient, instance, notif_type, message)


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
