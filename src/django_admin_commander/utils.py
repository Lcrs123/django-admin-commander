from collections.abc import Iterable
from functools import lru_cache
from typing import Literal, TypeAlias

from django.conf import LazySettings, settings

from .consts import ADMIN_COMMANDS_SETTINGS_NAME
from .exceptions import CommandsImproperlyConfigured

AppName: TypeAlias = str
CommandName: TypeAlias = str
Commands: TypeAlias = set[CommandName] | Literal["__all__"]
AdminCommandsSetting: TypeAlias = dict[AppName, Commands]
"""A dict whose keys are strings and values are either the literal "__all__" or an iterable of strings"""


@lru_cache(maxsize=None)
def get_admin_commands_setting(
    settings: LazySettings = settings,
    admin_commands_settings_name: str = ADMIN_COMMANDS_SETTINGS_NAME,
) -> AdminCommandsSetting:
    """Returns the value of the setting with the name defined in ADMIN_COMMANDS_SETTINGS_NAME or an empty dict if not defined.

    Caches and returns the cached value after the first run

    Args:
        settings (LazySettings, optional): The django lazy settings proxy that points to the project settings as defined in DJANGO_SETTINGS_MODULE. Defaults to settings.
        admin_commands_settings_name (str, optional): The expected settings name for django-admin-commands. Defaults to ADMIN_COMMANDS_SETTINGS_NAME.

    Raises:
        CommandsImproperlyConfigured: Raises default improperly configured exception if the setting or its keys and values not of the expected types

    Returns:
        AdminCommandsSetting: A dict whose keys are strings and values are either the literal "__all__" or an iterable of strings
    """
    admin_commands = getattr(settings, admin_commands_settings_name, dict())
    if not isinstance(admin_commands, dict):
        raise CommandsImproperlyConfigured(str(admin_commands))
    if not all(isinstance(app_name, str) for app_name in admin_commands.keys()):
        raise CommandsImproperlyConfigured(str(admin_commands),f"\n\nIdentified keys with wrong types: {[app_name for app_name in admin_commands.keys() if not isinstance(app_name,str)]}")
    for app_name, command_names in admin_commands.items():
        if isinstance(command_names, str) and command_names != "__all__":
            raise CommandsImproperlyConfigured(str(admin_commands), f"\n\nIdentified value with wrong type - key: '{app_name}', value: {command_names}")
        if not (
                isinstance(command_names, Iterable)
                and
                all(isinstance(command, str) for command in command_names)
            ):
            raise CommandsImproperlyConfigured(str(admin_commands), f"\n\nIdentified values with wrong types - key: '{app_name}', values: {command_names}")
    for app, commands in admin_commands.items():
        if commands != "__all__":
            admin_commands[app] = set(commands)
    return admin_commands
