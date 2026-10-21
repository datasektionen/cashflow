from decimal import Decimal
from typing import ClassVar, Unpack

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.timezone import localdate
from structlog import get_logger

from cashflow import dauth
from core.exceptions import (
    AlreadyAccountedError,
    CashflowVerificationMissingError,
    DuplicateConfirmationError,
    FlaggedAttestationError,
    FlaggedConfirmationError,
    FortnoxRecordMissingError,
    MismatchedTotalAmountError,
    NoAccountingMethodError,
    NotConfirmableError,
    NotConfirmedError,
    NotPayableError,
    SelfAttestationError,
    UnauthorizedAccountingError,
    UnauthorizedAttestationError,
    UnauthorizedConfirmationError,
    UnauthorizedUnconfirmationError,
)
from core.permissions import get_permission_provider
from fortnox import FortnoxAPIClient, FortnoxNotFound, VoucherRow
from notifications.notifications import get_notification_provider
lazy from core.search import ClaimSearchFields, claim_search
lazy from expenses.models import ExpenseData
lazy from fortnox.api_client.models import VoucherCreate
lazy from invoices.models import InvoiceData

logger = get_logger()


class Profile(models.Model):
    # The relation to the original django user
    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name="profile")

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


# Based of https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone
# noinspection PyUnusedLocal
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


# noinspection PyUnusedLocal
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class ClaimQuerySet(models.QuerySet["Claim"]):
    def expenses(self) -> ClaimQuerySet:
        return self.filter(type="expense").select_related("expense_data")

    def invoices(self) -> ClaimQuerySet:
        return self.filter(type="invoice").select_related("invoice_data")

    def attestable_for(self, user: User) -> ClaimQuerySet:

        # A user cannot attest their own expenses
        # (but they can attest their own invoices)
        qs = self.exclude(models.Q(type="expense") & models.Q(owner__user=user))
        if get_permission_provider().may_view_all(user):  # Sauron
            qs = qs.filter(part__attested_by__isnull=True)
        else:
            cost_centres = user.profile.attestable_cost_centres()
            qs = qs.filter(
                part__attested_by__isnull=True,
                part__cost_centre__in=cost_centres,
            )
        return qs.distinct()

    def accountable_for(self, user: User) -> ClaimQuerySet:
        qs = self.exclude(
            models.Q(type="expense", expense_data__reimbursement=None)
            | models.Q(type="invoice", invoice_data__paid_by=None)
        ).filter(verification="")

        if get_permission_provider().may_view_all(user):
            return qs.distinct()
        cost_centres = user.profile.accountable_cost_centres()
        return qs.filter(part__cost_centre__in=cost_centres).distinct()

    def confirmable_for(self, user: User) -> ClaimQuerySet:

        permissions = get_permission_provider()

        if not (permissions.may_confirm(user) or permissions.may_view_all(user)):
            return self.none()

        return self.filter(
            type="expense", expense_data__confirmed_by__isnull=True
        ).distinct()

    def payable_for(self, user: User) -> ClaimQuerySet:

        permissions = get_permission_provider()

        if not (permissions.may_pay(user) or permissions.may_view_all(user)):
            return self.none()

        return (
            self.filter(
                models.Q(type="expense", expense_data__reimbursement=None)
                | models.Q(type="invoice", invoice_data__paid_by=None)
            )
            .exclude(part__attested_by=None)
            .exclude(type="expense", expense_data__confirmed_by=None)
            .distinct()
        )

    def viewable_by(self, user: User) -> ClaimQuerySet:
        permissions = get_permission_provider()
        if (
            permissions.may_view_all(user)
            or permissions.may_pay(user)
            or permissions.may_confirm(user)
        ):
            return self.all()

        cost_centres = (
            set(permissions.viewable_cost_centres(user))
            | set(permissions.accountable_cost_centres(user))
            | set(permissions.attestable_cost_centres(user))
        )
        return self.filter(
            models.Q(part__cost_centre__in=cost_centres) | models.Q(owner__user=user)
        )

    def with_total(self) -> ClaimQuerySet:
        """Annotates each claim with the sum of its parts as `total`.

        Uses a subquery rather than Sum("part__amount") so that joins on parts
        added by filters can't duplicate rows in the sum, see
        https://docs.djangoproject.com/en/6.1/topics/db/aggregation/#combining-multiple-aggregations
        """
        return self.annotate(
            total=Coalesce(
                models.Subquery(
                    ClaimPart.objects.filter(claim=models.OuterRef("pk"))
                    .values("claim")
                    .annotate(t=models.Sum("amount"))
                    .values("t")
                ),
                models.Value(Decimal(0)),
            )
        )

    def search(self, **search_fields: Unpack[ClaimSearchFields]) -> ClaimQuerySet:
        return claim_search(self, **search_fields)


class Claim(models.Model):
    """A claim represents either an expense or an invoice.

    This model contains all shared fields for both types of user uploads.
    They are differentiated by the `invoice_data` and `expense_data`
    fields that are both nullable (a check ensures exactly one is not-null).
    """

    objects = ClaimQuerySet.as_manager()

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

    def __str__(self):
        return self.description

    @property
    def data_id(self) -> int:
        """The id of the claim's expense/invoice data, which is the id exposed
        through the API. It matches the pre-claim expense/invoice ids, so old
        links and Fortnox voucher descriptions remain valid."""
        data_id = self.expense_data_id or self.invoice_data_id
        assert data_id is not None
        return data_id

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

    # == Admin actions

    def total_amount(self) -> Decimal:
        return sum((part.amount for part in self.parts.all()), Decimal(0))

    def account(
        self,
        user: User,
        fortnox_client: FortnoxAPIClient | None = None,
        voucher_rows: list[VoucherRow] | None = None,
        voucher_number: str | None = None,
    ) -> str:
        """Accounts the claim (expense or invoice) either via Fortnox or by giving it an existing voucher number."""

        if not get_permission_provider().may_account(user, self):
            raise UnauthorizedAccountingError()

        if fortnox_client is not None:
            if self.expense_data is not None:
                voucher_series = settings.FORTNOX_EXPENSE_VOUCHER_SERIES
                transaction_date = self.expense_data.expense_date.strftime("%Y-%m-%d")
            else:
                assert self.invoice_data is not None
                voucher_series = settings.FORTNOX_INVOICE_VOUCHER_SERIES
                invoice_date = self.invoice_data.invoice_date
                transaction_date = (
                    invoice_date.strftime("%Y-%m-%d") if invoice_date else ""
                )

            description = settings.FORTNOX_DESCRIPTION_FORMAT.format(
                description=self.description, kind=self.type, id=self.data_id
            )
            if self.verification:
                try:
                    fortnox_client.retrieve_voucher(
                        voucher_series,
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

            # Verify total amount of voucher rows matches the total amount of the claim
            if voucher_rows is not None:
                voucher_total = sum(
                    (
                        Decimal(str(r.Debit))
                        for r in voucher_rows
                        if r.Debit is not None
                    ),
                    Decimal(0),
                )

                if voucher_total != self.total_amount():
                    logger.debug(
                        "mismatched total",
                        voucher_total=voucher_total,
                        claim_total=self.total_amount(),
                        voucher_rows=voucher_rows,
                    )
                    raise MismatchedTotalAmountError()

            created = fortnox_client.create_voucher(
                VoucherCreate(
                    Description=description,
                    TransactionDate=transaction_date,
                    VoucherRows=voucher_rows or [],
                    VoucherSeries=voucher_series,
                )
            )
            self.verification = f"{voucher_series}{created.VoucherNumber}"
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
        comment = Comment.objects.create(
            author=user.profile,
            claim=self,
            content=f"Bokförde med verifikationsnumret: {self.verification}",
        )

        get_notification_provider().on_comment(self, comment)

        return self.verification

    def is_payable(self) -> bool:
        """Whether this invoice is unpaid and all of its parts are attested."""
        if self.invoice_data is None or self.invoice_data.paid_at:
            return False
        return not self.parts.filter(attested_by__isnull=True).exists()

    def pay(self, user: User):
        if self.invoice_data is None:
            raise NotPayableError()

        self.invoice_data.paid_by = user.profile
        self.invoice_data.paid_at = timezone.localdate()
        self.invoice_data.save()

        comment = Comment.objects.create(
            author=user.profile,
            claim=self,
            content=f"Betalade fakturan ```{self}```",
        )

        get_notification_provider().on_comment(self, comment)

    def reset_confirmation(self):
        """Voids an existing confirmation, e.g. after the parts or files a
        confirmer signed off on have changed. A no-op for invoices."""
        if self.expense_data is not None and self.expense_data.confirmed_by_id:
            self.expense_data.confirmed_by = None
            self.expense_data.confirmed_at = None
            self.expense_data.save(update_fields=["confirmed_by", "confirmed_at"])

    def confirm(self, user: User):
        if not user.profile.may_confirm():
            raise UnauthorizedConfirmationError()

        # only expenses can be confirmed
        if self.type != "expense" or self.expense_data is None:
            raise NotConfirmableError()

        if self.expense_data.confirmed_by:
            raise DuplicateConfirmationError()

        if self.expense_data.is_flagged:
            raise FlaggedConfirmationError()

        self.expense_data.confirmed_by = user
        self.expense_data.confirmed_at = timezone.localdate()
        self.expense_data.save()
        comment = Comment.objects.create(
            author=user.profile,
            claim=self,
            content="Jag har bekräftat kvittots giltighet.",
        )
        get_notification_provider().on_comment(self, comment)

    def unconfirm(self, user: User):
        if not user.profile.may_unconfirm():
            raise UnauthorizedUnconfirmationError()
        if self.type != "expense" or self.expense_data is None:
            raise NotConfirmableError()
        if not self.expense_data.confirmed_by:
            raise NotConfirmedError()
        self.expense_data.confirmed_by = None
        self.expense_data.confirmed_at = None
        self.expense_data.save()


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
        # You are allowed to attest your own invoices, but not your own expenses
        if self.claim.type == "expense" and self.claim.owner == user.profile:
            raise SelfAttestationError()

        self.attested_by = user.profile
        self.attest_date = localdate()
        self.save()
        comment = Comment.objects.create(
            author=user.profile,
            claim=self.claim,
            content=f"Attesterar kvittodelen ```{self}```",
        )

        get_notification_provider().on_comment(self.claim, comment)

    def unattest(self, user: User):
        if self.cost_centre not in user.profile.attestable_cost_centres():
            raise UnauthorizedAttestationError()

        self.attested_by = None
        self.attest_date = None
        self.save()

        comment = Comment.objects.create(
            author=user.profile,
            claim=self.claim,
            content=f"Avattesterar kvittodelen ```{self}```",
        )

        get_notification_provider().on_comment(self.claim, comment)

    def __str__(self):
        return f"{self.claim} ({self.budget_line}: {self.amount} kr)"


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

    # The attached files are part of what a confirmer signs off on, so changing
    # them voids an existing confirmation. Note that bulk queryset operations
    # bypass this, like all model-level behaviour.

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.claim.reset_confirmation()

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        self.claim.reset_confirmation()
        return result
