from django.conf import settings


class StaticCORSHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_origins = getattr(settings, "ALLOWED_HOSTS", [])

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith(settings.STATIC_URL):
            origin = request.headers.get("Origin")
            if origin and any(origin.endswith(host) for host in self.allowed_origins):
                response["Access-Control-Allow-Origin"] = origin
                response["Vary"] = "Origin"

        return response
