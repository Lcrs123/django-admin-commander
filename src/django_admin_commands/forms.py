from copy import deepcopy

from django import forms
from django.core.management import get_commands

from .utils import AppName, CommandName, get_admin_commands, AdminCommandsSetting


def get_valid_command_choices(
    admin_commands: AdminCommandsSetting = get_admin_commands(),
) -> list[tuple[AppName, CommandName]]:
    """Returns a list of tuples with two strings, the app and respective command name, with the commands defined in the settings that are actually in the registered with django.

    Will return the actual command names for apps with commands set to '__all__' in the settings.

    Args:
        admin_commands (AdminCommandsSetting, optional): The dict with the settings value. Defaults to get_admin_commands().

    Returns:
        list[tuple[AppName, CommandName]]: A list of tuples with two strings, the app and respective command name,
    """
    all_commands_to_apps = get_commands()
    choice_mapping:dict[AppName, list[str]] =  {app: [] for app, _ in admin_commands if app in all_commands_to_apps.values()}
    for command, app in all_commands_to_apps.items():
        if app in admin_commands and (
            admin_commands[app] == "__all__" or command in admin_commands[app]
        ):
            choice_mapping[app].append(command)
    choices: list[tuple[AppName, CommandName]] = []
    for command, app in all_commands_to_apps.items():
        if app in admin_commands and (
            admin_commands[app] == "__all__" or command in admin_commands[app]
        ):
            choices.append((app, command))
    return choices


VALID_COMMAND_CHOICES = get_valid_command_choices()
OPT_GROUPS:dict[AppName, list[str]] = {
    app: [] for app, _ in VALID_COMMAND_CHOICES
}  # Using defaultdict does not work when iterating from template for some reason
"""Mapping from App to list of enabled commands. Used in template to group select options with optgroup html tag"""
for app, command in VALID_COMMAND_CHOICES:
    OPT_GROUPS[app].append(command)


class GroupedChoiceField(forms.ChoiceField):
    optgroups: dict[AppName, list[CommandName]]


class CommandForm(forms.Form):
    """Form for the admin run command view template"""
    command = GroupedChoiceField(
        choices=[(command, command) for _, command in VALID_COMMAND_CHOICES],
        required=True,
    )
    args = forms.CharField(label="Arguments (optional)", required=False)

    def __init__(self, *args, optgroups:dict[AppName, list[str]]=OPT_GROUPS, **kwargs) -> None:
        """Returns an instance of the form.

        Stores the value of optgroups in the form field 'command', which can be accessed in templates with 'form.command.optgroups'

        Args:
            optgroups (dict[AppName, list[str]], optional): Mapping from App to list of enabled commands. Defaults to OPT_GROUPS.
        """
        super().__init__(*args, **kwargs)
        # self.command.optgroups = deepcopy(optgroups)
        self["command"].optgroups = deepcopy(optgroups) # Deepcopy just to be sure and prevent any django strangeness from accidentally messing with the original dict in successive instantiations.
