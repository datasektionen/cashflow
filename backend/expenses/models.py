from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from structlog import get_logger

lazy from core.models import ClaimPart
lazy from core.models import Profile as CoreProfile

logger = get_logger()


class Payment(models.Model):
    """
    Represents a payment from a chapter account to a member.
    """

    date = models.DateField(auto_now_add=True)
    payer = models.ForeignKey(
        CoreProfile, related_name="payer", on_delete=models.DO_NOTHING
    )
    receiver = models.ForeignKey(
        CoreProfile, related_name="receiver", on_delete=models.DO_NOTHING
    )

    # Return a string representation of the payment
    def __str__(self):
        return f"Payment #{self.id} on {self.date} to {self.receiver}"

    # Returns the total amount of the payment
    def amount(self) -> Decimal:
        return ClaimPart.objects.filter(
            claim__expense_data__reimbursement=self
        ).aggregate(total=Coalesce(Sum("amount"), Value(Decimal(0))))["total"]

    # Returns the payment tag, which makes the payment identifiable in the bank
    def tag(self):
        return settings.PAYMENT_TAG_PREFIX + str(self.id)


class ExpenseData(models.Model):
    """
    Represents an expense. An expense contains expense parts and information
    about the expense.
    """

    expense_date = models.DateField()
    confirmed_by = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.DO_NOTHING
    )
    confirmed_at = models.DateField(blank=True, null=True, default=None)
    reimbursement = models.ForeignKey(
        Payment, blank=True, null=True, on_delete=models.DO_NOTHING
    )
    is_flagged = models.BooleanField(default=False)
