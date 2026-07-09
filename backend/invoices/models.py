from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q

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
    MismatchedTotalAmountError,
    NoAccountingMethodError,
)

if TYPE_CHECKING:
    from fortnox.api_client import FortnoxAPIClient, VoucherRow


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

    def is_attested(self):
        # Iterates instead of querying so prefetched parts are reused.
        return all(part.attested_by_id is not None for part in self.parts.all())

    def is_paid(self):
        return bool(self.payed_at and self.payed_by_id)

    # TODO
    def is_payable(self):
        if self.payed_at:
            return False
        for ip in self.parts.all():
            if ip.attested_by is None:
                return False
        return True

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
        voucher_rows: "list[VoucherRow] | None" = None,
        voucher_number: str | None = None,
    ) -> str:
        if not get_permission_provider().may_account(user, self):
            raise UnauthorizedAccountingError()

        if fortnox_client is not None:
            from django.conf import settings
            from fortnox import FortnoxNotFound
            from fortnox.api_client.models import VoucherCreate

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

            # Verify total amount of voucher rows matches the total amount of the invoice
            if voucher_rows is not None:
                voucher_total = sum(
                    (
                        Decimal(str(r.Debit))
                        for r in voucher_rows
                        if r.Debit is not None
                    ),
                    Decimal("0"),
                )

                if voucher_total != self.total_amount():
                    raise MismatchedTotalAmountError()

            created = fortnox_client.create_voucher(
                VoucherCreate(
                    Description=description,
                    TransactionDate=(
                        self.invoice_date.strftime("%Y-%m-%d")
                        if self.invoice_date
                        else ""
                    ),
                    VoucherRows=voucher_rows or [],
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
        else:
            # User didn't pass either an existing voucher number or voucher rows
            raise NoAccountingMethodError()

        self.save()
        from expenses.models import Comment

        Comment.objects.create(
            author=user.profile,
            invoice=self,
            content=f"Bokförde med verifikationsnumret: {self.verification}",
        )
        return self.verification

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
