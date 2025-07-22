from django.apps import apps
from django.core.checks import Error, Warning, register, CheckMessage
from django.core.management import get_commands

from .utils import get_admin_commands_setting
from .exceptions import (
    AppNotFoundError,
    CommandNotFoundError,
    NoCommandsFoundWarning,
    ConfigNotSetWarning,
)


@register()
def check_config_is_set(app_configs, **kwargs) -> list[Warning]:
    errors = []
    admin_commands = get_admin_commands_setting()
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
    admin_commands = get_admin_commands_setting()
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
    admin_commands = get_admin_commands_setting()
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
