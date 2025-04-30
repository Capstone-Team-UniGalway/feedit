from allauth.account.adapter import DefaultAccountAdapter
from allauth.mfa.models import Authenticator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


class CustomAccountAdapter(DefaultAccountAdapter):
    def get_password_reset_url(self, request, user, token):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        return request.build_absolute_uri(
            reverse(
                "account_reset_password_from_key",
                kwargs={
                    "uidb64": uid,
                    "token": token,
                },
            )
        )

    def get_reset_password_from_key_url(self, key):
        return reverse(
            "account_reset_password_from_key",
            kwargs={
                "uidb64": "%(uidb64)s",
                "token": "%(token)s",
            },
        )

    def add_mfa_device(self, user, device):
        """Sets mfa_enabled field to True when user enabled mfa"""
        user.mfa_enabled = True
        user.save(update_fields=["mfa_enabled"])
        super().add_mfa_device(user, device)

    def remove_mfa_device(self, user, device):
        """If no devices left, mark MFA as disabled"""
        if not Authenticator.objects.filter(user=user).exists():
            user.mfa_enabled = False
            user.save(update_fields=["mfa_enabled"])
        super().remove_mfa_device(user, device)
