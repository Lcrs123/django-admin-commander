import io

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.messages import add_message
from django.core.management import call_command
from django.http.request import HttpRequest
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path

from .forms import CommandForm
from .models import DummyCommandModel


class CommandAdmin(ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "",
                self.admin_site.admin_view(self.run_command_view),
                name="run-command",
            ),
        ]
        return custom_urls + urls

    def run_command_view(self, request: HttpRequest):
        if request.method == "POST":
            form = CommandForm(request.POST)
            if form.is_valid():
                command = form.cleaned_data["command"]
                args = form.cleaned_data["args"].split()
                output = io.StringIO()
                try:
                    call_command(command, *args, stdout=output)
                    add_message(request, 20, f"Command output:\n{output.getvalue()}")
                except Exception as e:
                    add_message(request, 30, f"Error: {e}")
                return redirect("admin:run-command")
        else:
            form = CommandForm()
        context = dict(self.admin_site.each_context(request), form=form)
        return TemplateResponse(request, "django_admin_commands/admin/run_command.html", context)

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
