from django.db import models


class SignalUser(models.Model):
    display_name = models.CharField(verbose_name="Display Name", max_length=255, null=False)
    source_name = models.CharField(verbose_name="Source Name", max_length=255, null=False)
    source_number = models.CharField(verbose_name="Source Number", max_length=255, null=False, primary_key=True)

    created_at = models.DateTimeField(verbose_name="Model created at", auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name="Model modified at", auto_now=True)

    is_registered = models.BooleanField(verbose_name="I a Registered user", default=False)
