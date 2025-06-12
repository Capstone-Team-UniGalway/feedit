from django.contrib.sessions.models import Session
from django.dispatch import receiver
from django.utils.timezone import now

# Allauth Signals
from allauth.account.signals import (
    password_set,
    password_changed,
    password_reset,
    email_changed,
)
from allauth.mfa.signals import (
    authenticator_added,
    authenticator_removed,
    authenticator_reset,
)


def logout_other_sessions(user, current_session_key):
    """Invalidate all sessions for user except current one."""
    for session in Session.objects.filter(expire_date__gt=now()):
        data = session.get_decoded()
        if (
            data.get("_auth_user_id") == str(user.id)
            and session.session_key != current_session_key
        ):
            session.delete()


# --- Security Event Handlers ---


@receiver(password_set)
@receiver(password_changed)
@receiver(password_reset)
@receiver(authenticator_added)
@receiver(authenticator_removed)
@receiver(authenticator_reset)
@receiver(email_changed)
def invalidate_sessions_after_sensitive_change(request, user, **kwargs):
    logout_other_sessions(user, request.session.session_key)
