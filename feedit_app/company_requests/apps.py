from django.apps import AppConfig


class RequestsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "company_requests"

    def ready(self):
        """Import signals when the app is ready."""
        __import__("company_requests.signals")
