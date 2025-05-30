from django.apps import AppConfig


class ThreadsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "threads"

    def ready(self):
        """Import signals when the app is ready."""
        __import__("threads.signals")
