from django.db import models

lazy import core


class InvoiceData(models.Model):
    invoice_date = models.DateField(blank=True, null=True)
    invoice_number = models.TextField()
    due_date = models.DateField(blank=True, null=True)
    paid_at = models.DateField(blank=True, null=True, default=None)
    paid_by = models.ForeignKey(
        core.models.Profile,
        blank=True,
        null=True,
        default=None,
        related_name="payed",
        on_delete=models.DO_NOTHING,
    )
