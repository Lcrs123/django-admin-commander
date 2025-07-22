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

![admin panel view](./screenshots/panel-view-history.png)

When you click `View` or `Run Management Commands`, you'll open a view where you can choose and execute the enabled commands.

![run command view](./screenshots/run-command-view.png)
![command groups](./screenshots/command-groups.png)

Once chosen, the command usage info is automatically shown below the `Run Command` button:

![usage info](./screenshots/usage-info.png)

Any command args can be passed in the `Arguments` field. If the command expects any user input, it can be passed in the `User Input` field and will be passed to the command when prompted to.

Once run, the result of the execution is shown as a message on top of the screen:

![command output](./screenshots/command-output-check.png)

If you click the `History` button and have the django admin view log entry [permission](#permissions) enabled explicitely or as a `superuser`, you'll be able to see all log entries for executed commands:

![history](./screenshots/history-view.png)

### Permissions

Aside from the regular admin view checks, `django-admin-commander` checks if the user has the custom `run_management_command` permission before allowing opening the run command view or running commands:

![permission](./screenshots/permission.png)

If the user is not a `superuser`, it must be specifically added to allow running commands and accessing the view.

For accesing the `History` view, the user must be a `superuser` or have the default django `"admin.view_logentry"` permission.

### Warning

Some commands are not suited to be run like this and may cause the response process or the server itself to hang, for example, the `django.core` command `test`. It's your responsibility to enable only the commands you actually want to be able to run from the admin panel.