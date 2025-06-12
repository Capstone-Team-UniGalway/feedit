# mention_tags.py

import re

from django import template
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.html import format_html

register = template.Library()
User = get_user_model()


@register.filter
def render_mentions(text):
    """
    Converts mention-like text in CKEditor content to user profile links.
    Matches both legacy HTML and plain-text @Full Name formats.
    """
    if not text:
        return ""

    # Match HTML-style mentions with user ID (reliable)
    html_mention_pattern = (
        r'<span class="mention" data-mention="@(.*?) \[(\d+)\]">@([^<]+)</span>'
    )

    def replace_html(match):
        username, user_id, display_text = match.groups()
        try:
            user = User.objects.get(id=user_id, is_active=True)
            url = reverse("account_public_profile", kwargs={"identifier": user.id})
            return format_html(
                '<a href="{}" class="mention" data-mention-id="{}">{}</a>',
                url,
                user.id,
                display_text,
            )
        except User.DoesNotExist:
            return format_html('<span class="mention">{}</span>', display_text)

    result = re.sub(html_mention_pattern, replace_html, text)
    return result


@register.simple_tag
def unread_mentions_count(user):
    if not user or not user.is_authenticated:
        return 0
    return user.mentions_received.filter(is_read=False).count()
