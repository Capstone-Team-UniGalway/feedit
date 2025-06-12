from django.contrib.auth import get_user_model
from django.db.models import Q


def get_mentionable_users_for(user, limit=50):
    """
    Returns a list of mentionable users (same company, excluding self),
    formatted for CKEditor mention feeds.
    """
    if not user or not user.is_authenticated:
        return []

    company = getattr(user, "workplace", None) or getattr(user, "company", None)
    if not company:
        return []

    users = (
        get_user_model()
        .objects.filter(Q(workplace=company) | Q(company=company), is_active=True)
        .exclude(id=user.id)
        .order_by("first_name")[:limit]
    )

    return [
        {"id": f"@{u.get_full_name()} [{u.id}]", "text": f"@{u.get_full_name()}"}
        for u in users
    ]
