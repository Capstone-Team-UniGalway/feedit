from django.conf import settings


def set_cors_headers(headers, path, url):
    origin = headers.get("Origin")
    allowed_hosts = getattr(settings, "ALLOWED_HOSTS", [])

    if origin and any(origin.endswith(host) for host in allowed_hosts):
        return [("Access-Control-Allow-Origin", origin), ("Vary", "Origin")]

    return []
