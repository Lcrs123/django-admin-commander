from collections.abc import Iterable
from functools import lru_cache
from typing import Literal, TypeAlias

from django.conf import LazySettings, settings
from django.core.exceptions import ImproperlyConfigured

from .consts import ADMIN_COMMANDS_SETTINGS_HINT, ADMIN_COMMANDS_SETTINGS_NAME

AppName: TypeAlias = str
CommandName: TypeAlias = str
Commands: TypeAlias = set[CommandName] | Literal["__all__"]


class CommandsImproperlyConfigured(ImproperlyConfigured):
    """Default ImproperlyConfigured exception"""
    def __init__(
        self,
        setting_values: str,
        message: str = f"Setting '{ADMIN_COMMANDS_SETTINGS_NAME}' is improperly configured. {ADMIN_COMMANDS_SETTINGS_HINT}",
    ) -> None:
        """ImproperlyConfigured exception with default message

        Args:
            setting_values (str): Should be the string value of the settings with the name defined in ADMIN_COMMANDS_SETTINGS_NAME
            message (str, optional): Default message for the exception. Defaults to f"Setting '{ADMIN_COMMANDS_SETTINGS_NAME}' is improperly configured. {ADMIN_COMMANDS_SETTINGS_HINT}".
        """
        super().__init__(message + f"The setting current values are {setting_values}")


@lru_cache(maxsize=None)
def get_admin_commands(
    settings: LazySettings = settings,
    admin_commands_settings_name: str = ADMIN_COMMANDS_SETTINGS_NAME,
) -> dict[AppName, Commands]:
    """Returns the value of the setting with the name defined in ADMIN_COMMANDS_SETTINGS_NAME or an empty dict if not defined.

    Caches and returns the cached value after the first run

    Args:
        settings (LazySettings, optional): The django lazy settings proxy that points to the project settings. Defaults to settings.
        admin_commands_settings_name (str, optional): The expected settings name for django-admin-commands. Defaults to ADMIN_COMMANDS_SETTINGS_NAME.

    Raises:
        CommandsImproperlyConfigured: Raises default improperly configured exception if the setting or its keys and values not of the expected types

    Returns:
        dict[AppName, Commands]: A dict whose keys are strings and values are either the literal "__all__" or an iterable of strings
    """
    admin_commands = getattr(settings, admin_commands_settings_name, dict())
    if not isinstance(admin_commands, dict):
        raise CommandsImproperlyConfigured(str(admin_commands))
    if not all(isinstance(key, str) for key in admin_commands.keys()):
        raise CommandsImproperlyConfigured(str(admin_commands))
    for command_names in admin_commands.values():
        if command_names == "__all__":
            continue
        if isinstance(command_names, Iterable) and all(
            isinstance(command, str) for command in command_names
        ):
            continue
        raise CommandsImproperlyConfigured(str(admin_commands))
    for app, commands in admin_commands.items():
        if commands != "__all__":
            admin_commands[app] = set(commands)
    return admin_commands
