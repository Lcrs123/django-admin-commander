from django.core.checks import Error, Warning
from django.core.management import get_commands
from django.conf import settings
from .consts import ADMIN_COMMANDS_SETTINGS_HINT, ADMIN_COMMANDS_SETTINGS_NAME, APP_NAME
from django.core.exceptions import ImproperlyConfigured, PermissionDenied


class AppNotFoundError(Error):
    def __init__(self, app_name: str, id: str = f"{APP_NAME}.E001") -> None:
        super().__init__(
            f"App '{app_name}' is not in INSTALLED_APPS",
            hint=f"The app name should be one of those in INSTALLED_APPS or 'django.core' for the django default commands. Apps currently in INSTALLED_APPS are: {getattr(settings,'INSTALLED_APPS',[])}",
            id=id,
        )


class CommandNotFoundError(Error):
    def __init__(
        self, app_name: str, command_name: str, id: str = f"{APP_NAME}.E002"
    ) -> None:
        super().__init__(
            f"Command named '{command_name}' not found for app '{app_name}'. The values should be a list of commands available for the app or '__all__' to enable all commands.",
            hint=f"Available commands for app '{app_name}' are {[command for command, app in get_commands().items() if app == app_name]}",
            id=id,
        )


class NoCommandsFoundWarning(Warning):
    def __init__(self, app_name: str, id: str = f"{APP_NAME}.W001") -> None:
        super().__init__(
            f"The config for App '{app_name}' is set to '__all__' but no commands were found for the app",
            id=id,
        )


class ConfigNotSetWarning(Warning):
    def __init__(self, id: str = f"{APP_NAME}.W002") -> None:
        super().__init__(
            f"Setting '{ADMIN_COMMANDS_SETTINGS_NAME}' is not set. No commands will be shown.",
            hint=ADMIN_COMMANDS_SETTINGS_HINT,
            id=id,
        )


class CommandsImproperlyConfigured(ImproperlyConfigured):
    """Default ImproperlyConfigured exception"""

    def __init__(
        self,
        setting_values: str,
        additional_info: str = "",
        default_message: str = f"Setting '{ADMIN_COMMANDS_SETTINGS_NAME}' is improperly configured.",
        hint: str = ADMIN_COMMANDS_SETTINGS_HINT
    ) -> None:
        """ImproperlyConfigured exception with default message

        Args:
            setting_values (str): Should be the string value of the settings with the name defined in ADMIN_COMMANDS_SETTINGS_NAME
            message (str, optional): Default message for the exception. Defaults to f"Setting '{ADMIN_COMMANDS_SETTINGS_NAME}' is improperly configured. {ADMIN_COMMANDS_SETTINGS_HINT}".
        """
        super().__init__(default_message + additional_info + f"\n\nThe setting current values are {setting_values}" + f"\n\nHINT: {hint}")


class RunCommandPermissionDenied(PermissionDenied):
    def __init__(
        self, msg: str = "User does not have permission to run commands"
    ) -> None:
        super().__init__(msg)


class ViewHistoryPermissionDenied(PermissionDenied):
    def __init__(
        self, msg: str = "User does not have permission to view execution history"
    ) -> None:
        super().__init__(msg)
