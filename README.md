# django-admin-commander

A Django app to run management commands from the admin panel with action logging and permission control.

## Installation

```
pip install django-admin-commander
```

## Usage

Add `"django_admin_commander"` to the end of `INSTALLED_APPS` in your project's `settings.py`:

```python
INSTALLED_APPS = [
    ...,
    "django_admin_commander",
]
```

Run `python manage.py migrate` to register the dummy [command model](https://github.com/Lcrs123/django-admin-commander/blob/master/src/django_admin_commander/models.py).

Next, add a setting named [`ADMIN_COMMANDS`](#admin_commands) to your project's settings.py. This setting should be a dictionary where:
- Keys are strings representing the app names.
- Values are either the string `"__all__"` to enable all commands for the app, or an iterable of strings specifying which commands to show.

To enable general Django commands, use the app name `"django.core"`. For example:

```python
ADMIN_COMMANDS = {
    "django.contrib.staticfiles": "__all__",
    "django.core": ["check", "diffsettings"],
    "django.contrib.sessions": "__all__",
}
```

That's it! Now, when you access the admin panel with the custom [permission](#permissions) enabled explicitly or as a `superuser`, you'll see a section for running management commands. Commands you've executed will also appear in your recent actions panel:

![admin panel view](https://github.com/Lcrs123/django-admin-commander/blob/master/screenshots/panel-view-history.png?raw=True)

Clicking `View` or `Run Management Commands` opens a view where you can choose and execute the enabled commands.

![run command view](https://github.com/Lcrs123/django-admin-commander/blob/master/screenshots/run-command-view.png?raw=True)
![command groups](https://github.com/Lcrs123/django-admin-commander/blob/master/screenshots/command-groups.png?raw=True)

Once selected, the command usage info is automatically displayed below the `Run Command` button:

![usage info](https://github.com/Lcrs123/django-admin-commander/blob/master/screenshots/usage-info.png?raw=True)

You can pass any command arguments in the `Arguments` field.

If the command expects user input, it can be provided in the `User Input` field and will be passed to the command when prompted.

> [!INFO]
> If you don't want to allow input to be passed to the command prompt, you can disable the `User Input` field entirely by setting [ADMIN_COMMANDS_ALLOW_USER_INPUT](#admin_commands_allow_user_input) to `False` in your project's `settings.py`.

After execution, the result is displayed as a message at the top of the screen:

![command output](https://github.com/Lcrs123/django-admin-commander/blob/master/screenshots/command-output-check.png?raw=True)

> [!CAUTION]
> Some commands are not suited to be run this way and may cause the response process to hang. For example, the `django.core` command `test`. It's your responsibility to enable only the commands you actually want to run from the admin panel.

Clicking the `History` button (with the appropriate [permission](#permissions) or as a `superuser`) lets you view all log entries for executed commands:

![history](https://github.com/Lcrs123/django-admin-commander/blob/master/screenshots/history-view.png?raw=True)

### Permissions

In addition to standard admin view checks, `django-admin-commander` verifies whether the user has the custom `run_management_command` permission before allowing access to the run command view or executing commands:

![permission](https://github.com/Lcrs123/django-admin-commander/blob/master/screenshots/permission.png?raw=True)

If the user is not a `superuser`, this permission must be explicitly granted.

To access the `History` view, the user must be a `superuser` or have the default Django `"admin.view_logentry"` permission.

### Settings

List of available settings:

#### `ADMIN_COMMANDS`

    A dictionary where keys are app names and values are either `'__all__'` to show all commands for the app or an iterable of command names to show. Default is an empty dictionary.

#### `ADMIN_COMMANDS_ALLOW_USER_INPUT`

    Set to `True` to allow user input to be passed to the command's stdin when prompted. Set to `False` to disable the field. Default is `True`.