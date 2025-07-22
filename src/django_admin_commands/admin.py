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
from .exceptions import RunCommandPermissionError


logger = logging.getLogger(__name__)


class CommandAdmin(ModelAdmin):
    object_history_template = "django_admin_commands/admin/commands_history.html"

    def get_urls(self):
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
        return custom_urls + urls

    def history_view(
        self, request: HttpRequest, object_id: str = "", extra_context: None = None
    ) -> HttpResponse:
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
    ):
        if not request.user.has_perm(f"{APP_NAME}.{PERMISSION_NAME}"):
            raise RunCommandPermissionError()
        if request.method == "POST":
            form = CommandForm(request.POST)
            if form.is_valid():
                command = form.cleaned_data["command"]
                args = form.cleaned_data["args"].split()
                stdin = form.cleaned_data["stdin"]
                logger.debug("Received command '%s' with args %s", command, args)
                for arg in default_command_args:
                    if arg not in args:
                        args.append(arg)
                        logger.debug("Appended arg '%s' to args", arg)
                output = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = output
                old_stdin = sys.stdin
                sys.stdin = io.StringIO(stdin)
                try:
                    call_command(command, *args, stdout=output, stderr=output)
                    add_message(request, 20, f"Command output:\n{output.getvalue()}")
                    self.log_execution_ok(request, command, args[:-2])
                except (Exception, SystemExit) as e:
                    if isinstance(e, SystemExit) and e.code == 0:
                        add_message(
                            request, 20, f"Command output:\n{output.getvalue()}"
                        )
                        self.log_execution_ok(request, command, args[:-2])
                    else:
                        add_message(request, 30, f"Error: {e}\n{output.getvalue()}")
                        self.log_execution_error(request, command, args[:-2])
                finally:
                    sys.stdout = old_stdout
                    sys.stdin = old_stdin
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
        message_template: str = "Successfully executed '{command_name}' with args {args}",
    ):
        self.log_execution(
            request,
            message_template.format_map({"command_name": command_name, "args": args}),
            1,
        )  # use action_flag 1 (ADDITION) to show default green '+' django icon on actions log

    def log_execution_error(
        self,
        request: HttpRequest,
        command_name: str,
        args: str = "",
        message_template: str = "Error running '{command_name}' with args {args}",
    ):
        self.log_execution(
            request,
            message_template.format_map({"command_name": command_name, "args": args}),
            3,
        )  # use action_flag 3 (DELETION) to show default red 'X' django icon on actions log

    def log_execution(self, request, message: str, action_flag: Literal[1, 3]):
        return LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(self.model).id,
            object_id="",
            object_repr=message,
            action_flag=action_flag,
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
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
