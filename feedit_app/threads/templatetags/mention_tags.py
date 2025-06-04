import re

from django import template
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.html import format_html

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
    # Pattern to match legacy @username mentions but to exclude @Username[123] format
    legacy_pattern = r"(?<![>\w])@([a-zA-Z0-9_]+(?: [a-zA-Z0-9_]+)?)(?!\[)"
    # Pattern to match HTML mentions with data-mention-id
    html_pattern = r'data-mention-id="(\d+)"[^>]*>@([^<]+)<'
    # Pattern to match legacy HTML mentions like "@Emp Two/a>"
    legacy_html_pattern = r"<(?:a|span)[^>]*>@?([a-zA-Z0-9_\s]+)</(?:a|span)>"
    User = get_user_model()

    def replace_new_mention(match):
        username = match.group(1).strip()
        user_id = match.group(2)

        try:
            # Try to find the user by ID
            user = User.objects.filter(id=user_id, is_active=True).first()

            if user:
                # If user found, create a link with user ID
                profile_url = reverse(
                    "account_public_profile", kwargs={"identifier": user.id}
                )
                return format_html(
                    '<a href="{}" class="mention" data-mention-id="{}">@{}</a>',
                    profile_url,
                    user.id,
                    username,
                )
        except Exception:
            pass

        # If user not found or error, still render as a mention but without a link
        return format_html('<span class="mention">@{}</span>', username)

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
                    is_active=True,
                ).first()
            except Exception:
                pass
        else:
            # Try first name match
            user = User.objects.filter(
                first_name__iexact=username, is_active=True
            ).first()

        if user:
            # If user found, include user ID in the mention
            profile_url = reverse(
                "account_public_profile", kwargs={"identifier": user.id}
            )
            return format_html(
                '<a href="{}" class="mention" data-mention-id="{}">@{}</a>',
                profile_url,
                user.id,
                username,
            )
        else:
            # If user not found, still render as a mention but without a link
            return format_html('<span class="mention">@{}</span>', username)

    def replace_html_mention(match):
        user_id = match.group(1)
        username = match.group(2).strip()

        try:
            # Try to find the user by ID
            user = User.objects.filter(id=user_id, is_active=True).first()

            if user:
                # If user found, create a link with user ID
                profile_url = reverse(
                    "account_public_profile", kwargs={"identifier": user.id}
                )
                return format_html(
                    '<a href="{}" class="mention" data-mention-id="{}">@{}</a>',
                    profile_url,
                    user.id,
                    username,
                )
        except Exception:
            pass

        # If user not found or error, still render as a mention but without a link
        return format_html('<span class="mention">@{}</span>', username)

    def replace_legacy_html_mention(match):
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
                    is_active=True,
                ).first()
            except Exception:
                pass
        else:
            # Try first name match
            user = User.objects.filter(
                first_name__iexact=username, is_active=True
            ).first()

        if user:
            # If user found, include user ID in the mention
            profile_url = reverse(
                "account_public_profile", kwargs={"identifier": user.id}
            )
            return format_html(
                '<a href="{}" class="mention" data-mention-id="{}">@{}</a>',
                profile_url,
                user.id,
                username,
            )
        else:
            # If user not found, still render as a mention but without a link
            return format_html('<span class="mention">@{}</span>', username)

    # Note: We've removed the redundant replace_simple_mention function
    # as it was duplicating the functionality of the replace_legacy_mention function

    # First replace HTML format mentions
    result = re.sub(html_pattern, replace_html_mention, text)
    # Then replace legacy HTML format mentions
    result = re.sub(legacy_html_pattern, replace_legacy_html_mention, result)
    # Then replace new format mentions
    result = re.sub(new_pattern, replace_new_mention, result)
    # Then replace legacy format mentions
    result = re.sub(legacy_pattern, replace_legacy_mention, result)
    return result


@register.inclusion_tag("components/threads/mention_input_tailwind.html")
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
