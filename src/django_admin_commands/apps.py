from django.apps import AppConfig


class AdminCommandsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_admin_commands"

    def ready(self) -> None:
        from . import checks

        return super().ready()
