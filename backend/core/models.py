from typing import ClassVar

from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import localdate

from cashflow import dauth
from core.exceptions import (
    FlaggedAttestationError,
    SelfAttestationError,
    UnauthorizedAttestationError,
)
from core.permissions import get_permission_provider
from notifications.notifications import get_notification_provider
lazy from expenses.models import ExpenseData
lazy from invoices.models import InvoiceData


class Profile(models.Model):
    # The relation to the original django user
    user = models.OneToOneField(
        User, on_delete=models.PROTECT, related_name="core_profile"
    )

    # Represents a bank account owned by the user
    bank_account = models.CharField(max_length=13, blank=True)

    sorting_number = models.CharField(max_length=6, blank=True)
    bank_name = models.CharField(max_length=30, blank=True)

    @property
    def has_bank_info(self) -> bool:
        """Whether the user can be paid: both account and clearing number set."""
        return bool(self.bank_account and self.sorting_number)

    # Return a string representation of the user
    def __str__(self):
        return self.user.first_name + " " + self.user.last_name

    def may_view_all(self):
        return get_permission_provider().may_view_all(self.user)

    def viewable_cost_centres(self):
        return get_permission_provider().viewable_cost_centres(self.user)

    def may_view_all_payments(self):
        return get_permission_provider().may_view_all_payments(self.user)

    def may_manage_fortnox(self):
        return dauth.has_unscoped_permission(dauth.Permission.MANAGE_FORTNOX, self.user)

    def may_attest(self, expense_part):
        return get_permission_provider().may_attest(self.user, expense_part.cost_centre)

    def may_attest_some(self):
        return get_permission_provider().may_attest_some(self.user)

    def attestable_cost_centres(self):
        return get_permission_provider().attestable_cost_centres(self.user)

    def may_view_attestable(self):
        return self.may_view_all() or self.may_attest_some()

    def may_unattest(self):
        return get_permission_provider().may_unattest(self.user)

    def may_pay(self):
        return get_permission_provider().may_pay(self.user)

    def may_view_payable(self):
        return self.may_view_all() or self.may_pay()

    def may_confirm(self):
        return get_permission_provider().may_confirm(self.user)

    def may_unconfirm(self):
        return self.may_confirm()

    def may_view_confirmable(self):
        return self.may_view_all() or self.may_confirm()

    def may_account(self, expense=None, invoice=None):
        target = expense or invoice
        if target is None:
            return False
        return get_permission_provider().may_account(self.user, target)

    def may_account_some(self):
        return get_permission_provider().may_account_some(self.user)

    def accountable_cost_centres(self):
        return get_permission_provider().accountable_cost_centres(self.user)

    def may_view_accountable(self):
        return self.may_view_all() or self.may_account_some()

    def may_flag(self):
        return self.may_attest_some() or self.may_pay()

    def may_delete(self):
        return get_permission_provider().may_delete(self.user)

    def may_edit_invoice(self):
        return get_permission_provider().may_edit_invoice(self.user)

    def may_delete_comment(self):
        return get_permission_provider().may_moderate_comments(self.user)

    def is_admin(self):
        return (
            self.may_attest_some()
            or self.may_pay()
            or self.may_confirm()
            or self.may_account_some()
            or self.may_view_all()
        )

    def may_be_viewed_by(self, user):
        return user.username == self.user.username or user.profile.is_admin()

    def may_view_expense(self, expense):
        return (
            expense.owner.user.username == self.user.username
            or self.may_view_all()
            or self.may_pay()
            or self.may_confirm()
            or self.may_account(expense=expense)
            or any(self.may_attest(ep) for ep in expense.parts.all())
        )

    def may_view_invoice(self, invoice):
        return (
            invoice.owner.user.username == self.user.username
            or self.may_view_all()
            or self.may_pay()
            or self.may_confirm()
            or self.may_account(invoice=invoice)
            or any(self.may_attest(ip) for ip in invoice.parts.all())
        )

    def may_firmatecknare(self):
        return get_permission_provider().may_firmatecknare(self.user)

    def may_view_account(self):
        return get_permission_provider().may_view_account(self.user)


class Claim(models.Model):
    """A claim represents either an expense or an invoice.

    This model contains all shared fields for both types of user uploads.
    They are differentiated by the `invoice_data` and `expense_data`
    fields that are both nullable (a check ensures exactly one is not-null).
    """

    owner = models.ForeignKey(Profile, on_delete=models.PROTECT)
    description = models.TextField()
    created_date = models.DateField(auto_now_add=True)
    verification = models.CharField(max_length=7, blank=True)

    expense_data = models.ForeignKey(ExpenseData, null=True, on_delete=models.PROTECT)
    invoice_data = models.ForeignKey(InvoiceData, null=True, on_delete=models.PROTECT)

    # since Django 5.0 we can have computed fields, so we use this to more easily check
    # if a claim is an expense or invoice
    type = models.GeneratedField(
        expression=models.Case(
            models.When(expense_data__isnull=False, then=models.Value("expense")),
            models.When(invoice_data__isnull=False, then=models.Value("invoice")),
        ),
        output_field=models.CharField(max_length=7),
        db_persist=False,
    )

    class Meta:
        constraints: ClassVar = [
            # Non-empty description
            models.CheckConstraint(
                condition=~models.Q(description=""), name="description-not-empty"
            ),
            # Either expense or invoice
            models.CheckConstraint(
                condition=(
                    models.Q(expense_data__isnull=True)
                    ^ models.Q(invoice_data__isnull=True)  # ^ := XOR
                ),
                name="either-expense-or-invoice",
            ),
        ]


class ClaimPart(models.Model):
    claim = models.ForeignKey(
        Claim,
        on_delete=models.CASCADE,
        related_name="parts",
        related_query_name="part",
    )

    cost_centre = models.TextField(blank=True)
    secondary_cost_centre = models.TextField(blank=True)
    budget_line = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    attested_by = models.ForeignKey(
        Profile, blank=True, null=True, on_delete=models.DO_NOTHING
    )
    attest_date = models.DateField(blank=True, null=True)

    def attest(self, user: User):

        if self.claim.expense_data and self.claim.expense_data.is_flagged:
            raise FlaggedAttestationError()

        if self.cost_centre not in user.profile.attestable_cost_centres():
            raise UnauthorizedAttestationError()
        if self.claim.owner == user.profile:
            raise SelfAttestationError()

        self.attested_by = user.core_profile
        self.attest_date = localdate()
        self.save()
        comment = Comment(
            author=user.core_profile,
            claim=self.claim,
            content="Attesterar kvittodelen ```" + str(self) + "```",
        )
        comment.save()

        get_notification_provider().on_comment(self.claim, comment)

    def unattest(self, user):
        self.attested_by = None
        self.attest_date = None

        if self.cost_centre not in user.profile.attestable_cost_centres():
            raise UnauthorizedAttestationError()

        self.save()

        comment = Comment(
            author=user.profile,
            expense=self.expense,
            content="Avattesterar kvittodelen ```" + str(self) + "```",
        )
        comment.save()

        get_notification_provider().on_comment(self.expense, comment)


class Comment(models.Model):
    claim = models.ForeignKey(
        Claim,
        on_delete=models.CASCADE,
    )
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Profile, on_delete=models.DO_NOTHING)
    content = models.TextField()

    class Meta:
        ordering: ClassVar = ["date"]


class File(models.Model):
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE)
    file = models.FileField()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._reset_confirmation()

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        self._reset_confirmation()
        return result
