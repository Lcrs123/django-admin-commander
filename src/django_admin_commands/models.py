from django.db import models

# Create your models here.


class DummyCommandModel(models.Model):
    class Meta:
        verbose_name = "Run Management Command"
        managed = False
