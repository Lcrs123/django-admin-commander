from django.db import models
from .consts import PERMISSION_NAME
# Create your models here.


class DummyCommandModel(models.Model):
    class Meta:
        verbose_name = "Run Management Command"
        managed = False
        default_permissions = []
        permissions = [(PERMISSION_NAME, "Can run management commands")]
