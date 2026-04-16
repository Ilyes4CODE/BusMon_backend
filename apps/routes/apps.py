from django.apps import AppConfig


class RoutesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.routes'

    def ready(self):
        # noqa: F401 — register trip signals
        from . import signals  # pylint: disable=import-outside-toplevel
