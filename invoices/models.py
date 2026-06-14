from datetime import date
from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.forms.models import model_to_dict

from core.permissions import get_permission_provider
from core.exceptions import (
    UnauthorizedAttestationError,
    UnauthorizedConfirmationError,
    UnauthorizedUnconfirmationError,
    NotConfirmedError,
    DuplicateConfirmationError,
    UnauthorizedAccountingError,
    AlreadyAccountedError,
    FortnoxRecordMissingError,
    CashflowVerificationMissingError,
)

if TYPE_CHECKING:
    from fortnox.api_client import FortnoxAPIClient


class InvoiceQuerySet(models.QuerySet["Invoice"]):
    def attestable_for(self, user: User) -> "InvoiceQuerySet":
        qs = self.filter(invoicepart__attested_by__isnull=True).exclude(
            owner__user=user
        )
        cost_centres = user.profile.attestable_cost_centres()
        if cost_centres is not True:
            qs = qs.filter(invoicepart__cost_centre__in=cost_centres)
        return qs.order_by("due_date").distinct()

    def accountable_for(self, user: User) -> "InvoiceQuerySet":
        qs = self.exclude(payed_at__isnull=True).filter(verification="")
        cost_centres = user.profile.accountable_cost_centres()
        if cost_centres is not True:
            qs = qs.filter(invoicepart__cost_centre__in=cost_centres)
        return qs.order_by("invoice_date").distinct()

    def confirmable_for(self, user: User) -> "InvoiceQuerySet":
        if not get_permission_provider().may_confirm(user):
            return self.none()
        return self.filter(confirmed_by__isnull=True).distinct()

    def payable_for(self, user: User) -> "InvoiceQuerySet":
        if not get_permission_provider().may_pay(user):
            return self.none()
        return (
            self.filter(payed_at__isnull=True, invoicepart__attested_by__isnull=False)
            .distinct()
            .order_by("due_date")
        )

    def viewable_by(self, user: User) -> "InvoiceQuerySet":
        provider = get_permission_provider()
        if provider.may_view_all(user):
            return self.all()
        cc_scopes = provider.viewable_cost_centres(user)
        return self.filter(
            Q(invoicepart__cost_centre__in=cc_scopes) | Q(owner__user=user)
        ).distinct()


class Invoice(models.Model):
    """
    Represents an invoice.
    """

    objects = InvoiceQuerySet.as_manager()

    created_date = models.DateField(auto_now_add=True)
    invoice_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    # TODO: Is there a better choice for on_delete?
    confirmed_by = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.DO_NOTHING
    )
    confirmed_at = models.DateField(blank=True, null=True, default=None)
    owner = models.ForeignKey("expenses.Profile", on_delete=models.DO_NOTHING)
    description = models.TextField()
    file_is_original = models.BooleanField()
    verification = models.CharField(max_length=7, blank=True)
    payed_at = models.DateField(blank=True, null=True, default=None)
    payed_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        default=None,
        related_name="payed",
        on_delete=models.DO_NOTHING,
    )

    # Returns a string representation of the invoice
    def __str__(self):
        return self.description

    # Returns a unicode representation of the invoice
    def __unicode__(self):
        return self.description

    # Returns a json dict from the invoice
    def __repr__(self):
        return str(self.to_dict())

    def status(self):
        if self.verification:
            return "Bokförd som " + str(self.verification)
        return "Oklart"

    def pay(self, user):
        self.payed_by = user
        self.payed_at = date.today()
        self.save()

        from expenses.models import Comment

        comment = Comment(
            author=user.profile,
            invoice=self,
            content="Betalade fakturan ```" + str(self) + "```",
        )
        comment.save()

    # Return the total amount of the invoice parts
    def total_amount(self):
        return sum([part.amount for part in self.parts.all()])  # return total

    # Returns the cost centres belonging to the invoice as a list [{ cost_centre: 'Name' }, ...]
    def cost_centres(self):
        return self.parts.order_by("cost_centre").values("cost_centre").distinct()

    def is_attested(self):
        return self.parts.filter(attested_by__isnull=True).count() == 0

    def is_paid(self):
        return bool(self.payed_at and self.payed_by)

    # TODO
    def is_payable(self):
        if self.payed_at:
            return False
        for ip in self.parts.all():
            if ip.attested_by is None:
                return False
        return True

    # Returns a dict representation of the model
    def to_dict(self):
        exp = model_to_dict(self)
        exp["invoice_parts"] = [
            part.to_dict() for part in InvoicePart.objects.filter(invoice=self)
        ]
        exp["owner_username"] = self.owner.user.username
        exp["owner_first_name"] = self.owner.user.first_name
        exp["owner_last_name"] = self.owner.user.last_name
        exp["amount"] = self.total_amount()
        exp["cost_centres"] = [
            cost_centre["cost_centre"] for cost_centre in self.cost_centres()
        ]
        return exp

    def confirm(self, user: User):
        if not user.profile.may_confirm():
            raise UnauthorizedConfirmationError()
        if self.confirmed_by:
            raise DuplicateConfirmationError()
        self.confirmed_by = user
        self.confirmed_at = date.today()
        self.save()

    def unconfirm(self, user: User):
        if not user.profile.may_unconfirm():
            raise UnauthorizedUnconfirmationError()
        if not self.confirmed_by:
            raise NotConfirmedError()
        self.confirmed_by = None
        self.confirmed_at = None
        self.save()

    def account(
        self,
        user: User,
        fortnox_client: "FortnoxAPIClient | None" = None,
        part_accounts: "dict[int, int] | None" = None,
        voucher_number: str | None = None,
    ):
        if not get_permission_provider().may_account(user, self):
            raise UnauthorizedAccountingError()

        if fortnox_client is not None:
            from django.conf import settings
            from fortnox import FortnoxNotFound
            from fortnox.api_client.models import VoucherCreate, VoucherRow

            description = settings.FORTNOX_DESCRIPTION_FORMAT.format(
                description=self.description, kind="invoice", id=self.id
            )
            if self.verification:
                try:
                    fortnox_client.retrieve_voucher(
                        settings.FORTNOX_INVOICE_VOUCHER_SERIES,
                        int(self.verification[1:]),
                    )
                    raise AlreadyAccountedError()
                except FortnoxNotFound:
                    raise FortnoxRecordMissingError()
            else:
                try:
                    fortnox_client.find_voucher(Description=description)
                    raise CashflowVerificationMissingError()
                except FortnoxNotFound:
                    pass

            voucher_rows = [
                VoucherRow(
                    Account=settings.FORTNOX_INVOICE_CREDIT_ACCOUNT,
                    Credit=float(self.total_amount()),
                )
            ]
            if part_accounts:
                for part in self.parts.all():
                    acct = part_accounts[part.id]
                    cc = fortnox_client.find_cost_center(Description=part.cost_centre)
                    voucher_rows.append(
                        VoucherRow(
                            Account=acct, CostCenter=cc.Code, Debit=float(part.amount)
                        )
                    )

            created = fortnox_client.create_voucher(
                VoucherCreate(
                    Description=description,
                    TransactionDate=(
                        self.invoice_date.strftime("%Y-%m-%d")
                        if self.invoice_date
                        else ""
                    ),
                    VoucherRows=voucher_rows,
                    VoucherSeries=settings.FORTNOX_INVOICE_VOUCHER_SERIES,
                )
            )
            self.verification = (
                f"{settings.FORTNOX_INVOICE_VOUCHER_SERIES}{created.VoucherNumber}"
            )
        elif voucher_number is not None:
            if self.verification:
                raise AlreadyAccountedError()
            self.verification = voucher_number
        elif self.verification:
            raise AlreadyAccountedError()

        if self.verification:
            self.save()
            from expenses.models import Comment

            Comment.objects.create(
                author=user.profile,
                invoice=self,
                content=f"Bokförde med verifikationsnumret: {self.verification}",
            )

    # # TODO
    @staticmethod
    def payable():
        return (
            Invoice.objects.filter(payed_at__isnull=True)
            .filter(invoicepart__attested_by__isnull=False)
            .distinct()
            .order_by("due_date")
        )


class InvoicePart(models.Model):
    """
    Defines an invoice part, which is a specification of a part of an invoice.
    """

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="parts",
        related_query_name="invoicepart",
    )
    cost_centre = models.TextField(blank=True)
    secondary_cost_centre = models.TextField(blank=True)
    budget_line = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    attested_by = models.ForeignKey(
        "expenses.Profile", blank=True, null=True, on_delete=models.DO_NOTHING
    )
    attest_date = models.DateField(blank=True, null=True)

    # Returns string representation of the model
    def __str__(self):
        return (
            self.invoice.__str__()
            + " ("
            + self.budget_line
            + ": "
            + str(self.amount)
            + " kr)"
        )

    # Returns unicode representation of the model
    def __unicode__(self):
        return (
            self.invoice.__unicode__()
            + " ("
            + self.budget_line
            + ": "
            + str(self.amount)
            + " kr)"
        )

    def attest(self, user: User):
        if self.cost_centre not in user.profile.attestable_cost_centres():
            raise UnauthorizedAttestationError()

        self.attested_by = user.profile
        self.attest_date = date.today()

        self.save()
        from expenses.models import Comment

        comment = Comment(
            author=user.profile,
            invoice=self.invoice,
            content="Attesterar fakturadelen ```" + str(self) + "```",
        )
        comment.save()

    # Returns dict representation of the model
    def to_dict(self):
        exp_part = model_to_dict(self)
        del exp_part["invoice"]
        if self.attested_by is not None:
            exp_part["attested_by_username"] = self.attested_by.user.username
            exp_part["attested_by_first_name"] = self.attested_by.user.first_name
            exp_part["attested_by_last_name"] = self.attested_by.user.last_name
        return exp_part
