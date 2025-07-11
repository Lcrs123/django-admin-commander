from django.apps import apps
from django.core.checks import Error, Warning, register, CheckMessage
from django.core.management import get_commands

from .consts import ADMIN_COMMANDS_SETTINGS_HINT, ADMIN_COMMANDS_SETTINGS_NAME
from .utils import get_admin_commands


class AppNotFoundError(Error):
    def __init__(self, app_name: str, id: str = "commands.E001") -> None:
        super().__init__(
            f"App '{app_name}' is not in INSTALLED_APPS",
            hint="The app name should be one of those in INSTALLED_APPS or 'django.core' for the django default commands",
            id=id,
        )


class CommandNotFoundError(Error):
    def __init__(
        self, app_name: str, command_name: str, id: str = "commands.E002"
    ) -> None:
        super().__init__(
            f"Command '{command_name}' not found for app '{app_name}'",
            hint=f"Avaliable commands for app '{app_name}' are {[command for command, app in get_commands().items() if app == app_name]}",
            id=id,
        )


class NoCommandsFoundWarning(Warning):
    def __init__(self, app_name: str, id: str = "commands.W001") -> None:
        super().__init__(
            f"The config for App '{app_name}' is set to '__all__' but no commands were found for the app",
            id=id,
        )


class ConfigNotSetWarning(Warning):
    def __init__(self, id: str = "commands.W002") -> None:
        super().__init__(
            f"Setting '{ADMIN_COMMANDS_SETTINGS_NAME}' is not set. No commands will be shown.",
            hint=ADMIN_COMMANDS_SETTINGS_HINT,
            id=id,
        )


@register()
def check_config_is_set(app_configs, **kwargs) -> list[Warning]:
    errors = []
    admin_commands = get_admin_commands()
    if not admin_commands:
        errors.append(ConfigNotSetWarning())
    return errors


@register()
def check_app_names(app_configs, **kwargs) -> list[Error]:
    """Checks if all app names in the ADMIN_COMMANDS settings are installed

    Args:
        app_configs (_type_): _description_

    Returns:
        _type_: _description_
    """
    errors = []
    admin_commands = get_admin_commands()
    for app_name in admin_commands:
        if apps.is_installed(app_name):
            continue
        elif app_name != "django.core":
            errors.append(AppNotFoundError(app_name))
    return errors


@register()
def check_command_names(app_configs, **kwargs) -> list[CheckMessage]:
    errors = []
    all_commands_to_apps = get_commands()
    admin_commands = get_admin_commands()
    for app_name, command_names in admin_commands.items():
        if command_names != "__all__":
            for command_name in command_names:
                if not (
                    command_name in all_commands_to_apps
                    and app_name == all_commands_to_apps[command_name]
                ):
                    errors.append(CommandNotFoundError(app_name, command_name))
        else:
            if app_name not in all_commands_to_apps.values():
                errors.append(NoCommandsFoundWarning(app_name))
    return errors
