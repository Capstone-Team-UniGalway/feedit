from django import template
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth import get_user_model
import re

register = template.Library()


@register.filter
def render_mentions(text):
    """
    Renders @mentions in text as links to user profiles.
    Handles both formats:
    1. New format: @Username[123] - with embedded user ID
    2. Legacy format: @Username - requires lookup by name

    Adds data-mention-id attribute with the user ID for better identification.

    Usage:
    {{ thread.content|render_mentions|safe }}
    """
    if not text:
        return ""

    # Pattern to match new format mentions: @Username[123]
    new_pattern = r"@([a-zA-Z0-9_\s]+)\[(\d+)\]"
    # Pattern to match legacy @username mentions
    legacy_pattern = r"@([a-zA-Z0-9_\s]+)(?!\[\d+\])"
    User = get_user_model()

    def replace_new_mention(match):
        username = match.group(1).strip()
        user_id = match.group(2)

        try:
            # Try to find the user by ID
            user = User.objects.filter(id=user_id, is_active=True).first()

            if user:
                # If user found, create a link with user ID
                profile_url = reverse('account_profile') + f"?user={user.id}"
                return format_html(
                    '<a href="{}" class="mention" data-mention-id="{}">@{}</a>',
                    profile_url, user.id, username
                )
        except Exception:
            pass

        # If user not found or error, still render as a mention but without a link
        return format_html(
            '<span class="mention">@{}</span>', username
        )

    def replace_legacy_mention(match):
        username = match.group(1).strip()

        # Try to find the user by name
        user = None
        if " " in username:
            # Try full name match
            try:
                first_name, last_name = username.split(" ", 1)
                user = User.objects.filter(
                    first_name__iexact=first_name,
                    last_name__iexact=last_name,
                    is_active=True
                ).first()
            except Exception:
                pass
        else:
            # Try first name match
            user = User.objects.filter(
                first_name__iexact=username,
                is_active=True
            ).first()

        if user:
            # If user found, include user ID in the mention
            profile_url = reverse('account_profile') + f"?user={user.id}"
            return format_html(
                '<a href="{}" class="mention" data-mention-id="{}">@{}</a>',
                profile_url, user.id, username
            )
        else:
            # If user not found, still render as a mention but without a link
            return format_html(
                '<span class="mention">@{}</span>', username
            )

    # First replace new format mentions
    result = re.sub(new_pattern, replace_new_mention, text)
    # Then replace legacy format mentions
    result = re.sub(legacy_pattern, replace_legacy_mention, result)
    return result


@register.inclusion_tag("components/mention_input_tailwind.html")
def mention_input(
    name, id=None, value=None, css_class="", placeholder=None, required=False
):
    """
    Renders a textarea with @mention support using Tailwind CSS.

    Usage:
    {% mention_input name="content" id="thread_content" value=form.content.value
    css_class="h-32" %}
    """
    return {
        "name": name,
        "id": id,
        "value": value,
        "css_class": css_class,
        "placeholder": placeholder,
        "required": required,
    }


@register.simple_tag
def unread_mentions_count(user):
    """
    Returns the count of unread mentions for a user.

    Usage:
    {% unread_mentions_count user as count %}
    """
    if not user or not user.is_authenticated:
        return 0
    return user.mentions_received.filter(is_read=False).count()
