import io
import logging
import sys
from typing import Literal
from django.utils.translation import gettext as _

from django.utils.text import capfirst
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.models import LogEntry
from django.contrib.admin.options import get_content_type_for_model
from django.contrib.messages import add_message
from django.core.management import call_command
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.contrib.admin.views.main import PAGE_VAR

from .forms import CommandForm
from .models import DummyCommandModel
from .consts import APP_NAME, PERMISSION_NAME
from .exceptions import RunCommandPermissionDenied, ViewHistoryPermissionDenied

from django.urls.resolvers import URLPattern


logger = logging.getLogger(__name__)


class CommandAdmin(ModelAdmin):
    """Customized ModelAdmin for running management commands from the admin panel"""

    object_history_template = "django_admin_commands/admin/commands_history.html"

    def get_urls(self) -> list[URLPattern]:
        """Adds the run-command and admin-commands-history views to the modeladmin urls and returns the list of urlpatterns.

        The added views are wrapped in 'self.admin_site.admin_view' and treated as admin views, meaning by default they are never cached and only allow active staff users to acces the view.

        Returns:
            list[URLPattern]: _description_
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                "",
                self.admin_site.admin_view(self.run_command_view),
                name="run-command",
            ),
            path(
                "history",
                self.admin_site.admin_view(self.history_view),
                name="admin-commands-history",
            ),
        ]
        return (
            custom_urls + urls
        )  # Keep the custom_urls before default ones, as suggested in the django docs (https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.get_urls).

    def history_view(
        self, request: HttpRequest, object_id: str = "", extra_context: None = None
    ) -> HttpResponse:
        """View for the execution history.

        Mostly copied from the default history_view method from the ModelAdmin class
        and adapted for the fact that there is no saved object, since we use a dummy
        unmanaged model.

        Args:
            request (HttpRequest): _description_
            object_id (str, optional): _description_. Defaults to "".
            extra_context (None, optional): _description_. Defaults to None.

        Raises:
            ViewHistoryPermissionDenied: Raises PermissionDenied if the user does not have permission to view log entries.

        Returns:
            HttpResponse: _description_
        """
        if not self.has_view_logentry_permission(request):
            raise ViewHistoryPermissionDenied()
        model = self.model
        action_list = (
            LogEntry.objects.filter(
                object_id="",
                content_type=get_content_type_for_model(model),
            )
            .select_related()
            .order_by("-action_time")
        )
        paginator = self.get_paginator(request, action_list, 100)
        page_number = request.GET.get(PAGE_VAR, 1)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(page_obj.number)
        context = {
            **self.admin_site.each_context(request),
            "title": _("Execution history: %s") % self.model._meta.verbose_name,
            "subtitle": None,
            "action_list": page_obj,
            "page_range": page_range,
            "page_var": PAGE_VAR,
            "pagination_required": paginator.count > 100,
            "module_name": str(capfirst(self.opts.verbose_name_plural)),
            "object": self.model,
            "opts": self.opts,
            "preserved_filters": self.get_preserved_filters(request),
            **(extra_context or {}),
        }
        request.current_app = self.admin_site.name
        return TemplateResponse(
            request,
            self.object_history_template,
            context,
        )

    def run_command_view(
        self,
        request: HttpRequest,
        default_command_args: list[str] = ["--traceback", "--no-color"],
    ) -> HttpResponse:
        """View for running commands. Requires the user to have the run commands permission.

        Args:
            request (HttpRequest): _description_
            default_command_args (list[str], optional): Automatically added to command args if not already present. '--no-color' prevents unicode errors in the message shown to the user after execution. '--traceback' ensures full error message for the user. Defaults to ["--traceback", "--no-color"].

        Raises:
            RunCommandPermissionDenied: Raises PermissionDenied if user does not has permission for running commands.

        Returns:
            HttpResponse: _description_
        """
        if not self.has_run_command_permission(request):
            raise RunCommandPermissionDenied()
        if request.method == "POST":
            form = CommandForm(request.POST)
            if form.is_valid():
                command = form.cleaned_data["command"]
                args = form.cleaned_data["args"].split()
                stdin = form.cleaned_data["stdin"]
                logger.debug(
                    "Received command name '%s' with args '%s' and stdin '%s'",
                    command,
                    args,
                    stdin,
                )
                final_args = list(args)
                for arg in default_command_args:
                    if arg not in final_args:
                        final_args.append(arg)
                        logger.debug("Appended arg '%s' to final args", arg)
                output = io.StringIO()
                old_stdout, old_stdin = (
                    sys.stdout,
                    sys.stdin,
                )  # Storing for restoring afterwards
                sys.stdout = output  # Simply calling commands with 'stdout=output, stderr=output' was still leaving some text sent to terminal uncaptured, ex: running any command with '--version' or '--help'.
                sys.stdin = io.StringIO(
                    stdin
                )  # Some commands like 'collecstatic' which expect user input will hold indefinitely if stdin is not supplied.
                try:
                    logger.debug(
                        "Calling command '%s' with args %s and stdin '%s'",
                        command,
                        final_args,
                        stdin,
                    )
                    call_command(command, *final_args, stdout=output, stderr=output)
                    add_message(request, 20, f"Command output:\n{output.getvalue()}")
                    self.log_execution_ok(request, command, args)
                except (Exception, SystemExit) as e:
                    # Some commands cause SystemExit with code 0 on successful execution depending on args.
                    # Since they didn't actually error out, treat as successful.
                    if isinstance(e, SystemExit) and e.code == 0:
                        add_message(
                            request, 20, f"Command output:\n{output.getvalue()}"
                        )
                        self.log_execution_ok(request, command, args)
                    else:
                        add_message(request, 30, f"Error: {e}\n{output.getvalue()}")
                        self.log_execution_error(request, command, args)
                finally:
                    sys.stdout, sys.stdin = (
                        old_stdout,
                        old_stdin,
                    )  # Restoring original values
                return redirect("admin:run-command")
        else:
            form = CommandForm()
        context = dict(self.admin_site.each_context(request), form=form)
        return TemplateResponse(
            request, "django_admin_commands/admin/run_command.html", context
        )

    def log_execution_ok(
        self,
        request: HttpRequest,
        command_name: str,
        args: str = "",
        stdin: str = "",
        message_template: str = "Successfully executed '{command_name}' with args {args} and stdin {stdin}",
        action_flag: Literal[
            1, 3
        ] = 1,  # use action_flag 1 (ADDITION) to show default green '+' django icon on actions log
    ) -> LogEntry:
        """Log successful execution of command

        Args:
            request (HttpRequest): _description_
            command_name (str): _description_
            args (str, optional): _description_. Defaults to "".
            message_template (str, optional): _description_. Defaults to "Successfully executed '{command_name}' with args {args}".
            action_flag (Literal[ 1, 3 ], optional): _description_. Defaults to 1.

        Returns:
            LogEntry: _description_
        """
        return self.log_execution(
            request,
            message_template.format_map(
                {"command_name": command_name, "args": args, "stdin": stdin}
            ),
            action_flag,
        )

    def log_execution_error(
        self,
        request: HttpRequest,
        command_name: str,
        args: str = "",
        stdin: str = "",
        message_template: str = "Error running '{command_name}' with args {args} and stdin {stdin}",
        action_flag: Literal[
            1, 3
        ] = 3,  # use action_flag 3 (DELETION) to show default red 'X' django icon on actions log
    ) -> LogEntry:
        """Log execution of command with error

        Args:
            request (HttpRequest): _description_
            command_name (str): _description_
            args (str, optional): _description_. Defaults to "".
            message_template (str, optional): _description_. Defaults to "Error running '{command_name}' with args {args}".
            action_flag (Literal[ 1, 3 ], optional): _description_. Defaults to 3.

        Returns:
            LogEntry: _description_
        """
        return self.log_execution(
            request,
            message_template.format_map(
                {"command_name": command_name, "args": args, "stdin": stdin}
            ),
            action_flag,
        )

    def log_execution(
        self, request: HttpRequest, message: str, action_flag: Literal[1, 3]
    ) -> LogEntry:
        """Saves and returns a log entry with the passed message.

        The object_id for the log entry is set to "", since we dont actually store anything from our dummy command model.

        Args:
            request (HttpRequest): Request with the user set
            message (str): Message to be stored in the log entry.
            action_flag (Literal[1, 3]): 1 is the flag for ADDITION and 3 is the flag for DELETION.

        Returns:
            LogEntry: The saved log entry.
        """
        assert request.user.pk is not None, (
            "User must exist in database to be able to save log entry"
        )
        return LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(self.model).id,
            object_id="",
            object_repr=message,
            action_flag=action_flag,
        )

    def has_add_permission(self, request):
        """Always returns False. Causes the "add" hyperlink to be removed from the admin panel. Overrides default method."""
        return False

    def has_change_permission(self, request, obj=None):
        """Always returns False. Overrides default method."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Always returns False. Overrides default method."""
        return False

    def has_view_permission(self, request, obj=None):
        """Always returns True. Causes the "view" hyperlink to be shown on the admin panel and makes the "Run Management Command" model verbose name clickable. Overrides default method."""
        return True

    def has_permission(self, request: HttpRequest, full_permission_name: str) -> bool:
        """Check if user in request has permission with given full_permission_name

        Args:
            request (HttpRequest): _description_
            full_permission_name (str): The full permission name to check. Usually in the format 'app_name.permission_name'

        Returns:
            bool: True if user has the permission, False otherwise
        """
        return request.user.has_perm(full_permission_name)

    def has_run_command_permission(
        self,
        request: HttpRequest,
        full_permission_name: str = f"{APP_NAME}.{PERMISSION_NAME}",
    ) -> bool:
        """Check if user in request has permission for running commands.

        Args:
            request (HttpRequest): _description_
            full_permission_name (str, optional): _description_. Defaults to f"{APP_NAME}.{PERMISSION_NAME}".

        Returns:
            bool: True if user has the permission, False otherwise
        """
        return self.has_permission(request, full_permission_name)

    def has_view_logentry_permission(
        self, request: HttpRequest, full_permission_name: str = "admin.view_logentry"
    ) -> bool:
        """Check if user in request has permission for viewing log entries

        Args:
            request (HttpRequest): _description_
            full_permission_name (str, optional): _description_. Defaults to "admin.view_logentry".

        Returns:
            bool: True if user has the permission, False otherwise
        """
        return self.has_permission(request, full_permission_name)


@admin.register(DummyCommandModel)
class Commands(CommandAdmin):
    pass
