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
    object_history_template = "django_admin_commands/admin/history.html"

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

        if not request.user.has_perm(f"{APP_NAME}.{PERMISSION_NAME}"):
            raise RunCommandPermissionError()
        if request.method == "POST":
            form = CommandForm(request.POST)
            if form.is_valid():
                command = form.cleaned_data["command"]
                args = form.cleaned_data["args"].split()
                output = io.StringIO()
                try:
                    call_command(command, *args, stdout=output, stderr=output)
                    add_message(request, 20, f"Command output:\n{output.getvalue()}")
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=get_content_type_for_model(DummyCommandModel).id,
                        object_id="",
                        object_repr=f"Successfully executed '{command}' with args {args}",
                        action_flag=1, # use action_flag 1 (ADDITION) to show default green '+' django icon on actions log
                    )
                except Exception as e:
                    add_message(request, 30, f"Error: {e}")
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=get_content_type_for_model(DummyCommandModel).id,
                        object_id="",
                        object_repr=f"Error running '{command}' with args {args}",
                        action_flag=3, # use action_flag 3 (DELETION) to show default red 'X' django icon on actions log
                    )
                return redirect("admin:run-command")
        else:
            form = CommandForm()
        context = dict(self.admin_site.each_context(request), form=form)
        return TemplateResponse(
            request, "django_admin_commands/admin/run_command.html", context
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True


@admin.register(DummyCommandModel)
class Commands(CommandAdmin):
    pass
