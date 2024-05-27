from django.db import models
from core.models.signal_user import SignalUser


class SignalGroup(models.Model):
    name = models.CharField(verbose_name="Group Name", max_length=255, null=False)
    signal_id = models.CharField(verbose_name="Signal ID", max_length=255, null=False)
    internal_id = models.CharField(verbose_name="Internal ID", max_length=255, null=False, primary_key=True)

    members = models.ManyToManyField(
        to=SignalUser,
        related_name="groups"
    )

    owner = models.ForeignKey(
        to=SignalUser,
        on_delete=models.PROTECT,
        related_name="owned_groups"
    )

    created_at = models.DateTimeField(verbose_name="Model created at", auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name="Model modified at", auto_now=True)
