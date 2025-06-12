import bleach

ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "blockquote",
    "a",
    "span",
    "h1",
    "h2",
    "h3",
    "pre",
    "code",
    "table",
    "thead",
    "tbody",
    "tr",
    "td",
    "th",
    "hr",
    # Add "img" if needed
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "class", "data-mention-id"],
    "span": ["class", "data-mention"],
    "td": ["colspan", "rowspan", "style"],
    "th": ["colspan", "rowspan", "style"],
    "table": ["style"],
    # "img": ["src", "alt", "title"]  # Only if you allow image uploads
}


def sanitize_html(html):
    """Sanitize rich text input (CKEditor) while preserving mentions."""
    return bleach.clean(
        html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True
    )
