from django import template
from django.utils.html import format_html
from django.urls import reverse
import re

register = template.Library()


@register.filter
def render_mentions(text):
    """
    Renders @mentions in text as links to user profiles.

    Usage:
    {{ thread.content|render_mentions|safe }}
    """
    # Pattern to match @username mentions
    pattern = r"@([a-zA-Z0-9_\s]+)"

    def replace_mention(match):
        username = match.group(1).strip()
        profile_url = f"{reverse('account_profile')}?user_name={username}"
        return format_html(
            '<a href="{}" class="mention">@{}</a>', profile_url, username
        )

    # Replace mentions with links
    result = re.sub(pattern, replace_mention, text)
    return result


@register.inclusion_tag("components/mention_input.html")
def mention_input(
    name, id=None, value=None, css_class="", placeholder=None, required=False
):
    """
    Renders a textarea with @mention support.

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
