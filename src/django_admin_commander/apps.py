from django.apps import AppConfig
from .consts import APP_NAME


class AdminCommandsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = APP_NAME
    verbose_name = APP_NAME.replace("_", " ").title()

    def ready(self) -> None:
        from . import checks

        return super().ready()
