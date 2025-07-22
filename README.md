# django-admin-commander

A Django app to run management commands from the admin panel

## Installation

```
pip install django-admin-commander
```

## Usage

Add `"django_admin_commander"` to the end of `INSTALLED_APPS` in your project's `settings.py` :

```python
INSTALLED_APPS = [
    ...,
    "django_admin_commander",
]
```

Run `python manage.py migrate` to register our dummy [command model](./src/django_admin_commander/models.py).

Now add a setting named `ADMIN_COMMANDS` to your project `settings.py`. The setting should be a dict with keys as strings with the app names you want to enable commands for and the mapped values should be either the string literal `'__all__'` to show all commands for the app or an iterable of strings with the command names to show. To enable general django commands, use the app name `django.core`, for example:

```python
ADMIN_COMMANDS = {
    "django.contrib.staticfiles": "__all__",
    "django.core": ["check", "diffsettings"],
    "django.contrib.sessions": "__all__",
}
```

That's it! Now, when you access the admin panel with our custom [permission](#permissions) enabled explicitely or as a `superuser`, you'll see a section for running management commands. Commands you have tried to run will also be shown on your recent actions panel:

![admin panel view](https://github.com/Lcrs123/django-admin-commander/blob/master/screenshots/panel-view-history.png?raw=True)

When you click `View` or `Run Management Commands`, you'll open a view where you can choose and execute the enabled commands.

![run command view](https://github.com/Lcrs123/django-admin-commander/blob/master/screenshots/run-command-view.png?raw=True)
![command groups](https://github.com/Lcrs123/django-admin-commander/blob/master/screenshots/command-groups.png?raw=True)

Once chosen, the command usage info is automatically shown below the `Run Command` button:

![usage info](https://github.com/Lcrs123/django-admin-commander/blob/master/screenshots/usage-info.png?raw=True)

Any command args can be passed in the `Arguments` field. If the command expects any user input, it can be passed in the `User Input` field and will be passed to the command when prompted to.

Once run, the result of the execution is shown as a message on top of the screen:

![command output](https://github.com/Lcrs123/django-admin-commander/blob/master/screenshots/command-output-check.png?raw=True)

> [!CAUTION]
> Some commands are not suited to be run like this and may cause the response process to hang, for example, the `django.core` command `test`. It's your responsibility to enable only the commands you actually want to be able to run from the admin panel.

If you click the `History` button and have the django admin view log entry [permission](#permissions) enabled explicitely or as a `superuser`, you'll be able to see all log entries for executed commands:

![history](https://github.com/Lcrs123/django-admin-commander/blob/master/screenshots/history-view.png?raw=True)

### Permissions

Aside from the regular admin view checks, `django-admin-commander` checks if the user has the custom `run_management_command` permission before allowing opening the run command view or running commands:

![permission](https://github.com/Lcrs123/django-admin-commander/blob/master/screenshots/permission.png?raw=True)

If the user is not a `superuser`, it must be specifically added to allow running commands and accessing the view.

For accesing the `History` view, the user must be a `superuser` or have the default django `"admin.view_logentry"` permission.
