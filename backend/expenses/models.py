from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.db import models
from structlog import get_logger

if TYPE_CHECKING:
    from fortnox.api_client import FortnoxAPIClient, VoucherRow
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.timezone import localdate
from cashflow import email_util
from core.permissions import get_permission_provider
from core.exceptions import (
    UnauthorizedAttestationError,
    SelfAttestationError,
    FlaggedAttestationError,
    UnauthorizedConfirmationError,
    UnauthorizedUnconfirmationError,
    NotConfirmedError,
    DuplicateConfirmationError,
    FlaggedConfirmationError,
    UnauthorizedAccountingError,
    AlreadyAccountedError,
    FortnoxRecordMissingError,
    CashflowVerificationMissingError,
    MismatchedTotalAmountError,
    NoAccountingMethodError,
)

logger = get_logger()


class Profile(models.Model):
    """
    A profile is attached to each user to be able to store more information
    and relations with it.
    """

    # The relation to the original django user
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)

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

    def may_view_all_payments(self):
        return get_permission_provider().may_view_all_payments(self.user)

    def may_manage_fortnox(self):
        from cashflow import dauth

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

    def may_delete_expense(self, expense):
        if expense.reimbursement:
            return False
        return (
            get_permission_provider().may_delete(self.user)
            or expense.owner.user.username == self.user.username
        )

    def may_edit_invoice(self):
        return get_permission_provider().may_edit_invoice(self.user)

    def may_delete_invoice(self, invoice):
        if invoice.is_paid():
            return False
        return (
            get_permission_provider().may_delete(self.user)
            or invoice.owner.user.username == self.user.username
        )

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


class Payment(models.Model):
    """
    Represents a payment from a chapter account to a member.
    """

    date = models.DateField(auto_now_add=True)
    payer = models.ForeignKey(
        Profile, related_name="payer", on_delete=models.DO_NOTHING
    )
    receiver = models.ForeignKey(
        Profile, related_name="receiver", on_delete=models.DO_NOTHING
    )

    # Return a string representation of the payment
    def __str__(self):
        return f"Payment #{self.id} on {self.date} to {self.receiver}"

    # Returns the total amount of the payment
    def amount(self):
        total = 0
        for expense in Expense.objects.filter(reimbursement=self):
            total += expense.total_amount()
        return total

    # Returns the payment tag, which makes the payment identifiable in the bank
    def tag(self):
        return "Data" + str(self.id)


class ExpenseQuerySet(models.QuerySet["Expense"]):

    def attestable_for(self, user: User) -> "ExpenseQuerySet":
        qs = (
            self.filter(expensepart__attested_by__isnull=True)
            .exclude(is_flagged=True)
            .exclude(owner__user=user)
        )
        cost_centres = user.profile.attestable_cost_centres()
        if cost_centres is not True:
            qs = qs.filter(expensepart__cost_centre__in=cost_centres)
        return qs.order_by("id", "expense_date").distinct()

    def accountable_for(self, user: User) -> "ExpenseQuerySet":
        qs = self.exclude(reimbursement=None).filter(verification="")
        cost_centres = user.profile.accountable_cost_centres()
        if cost_centres is not True:
            qs = qs.filter(expensepart__cost_centre__in=cost_centres)
        return qs.order_by("expense_date").distinct()

    def confirmable_for(self, user: User) -> "ExpenseQuerySet":
        if not get_permission_provider().may_confirm(user):
            return self.none()
        return (
            self.filter(confirmed_by__isnull=True).exclude(is_flagged=True).distinct()
        )

    def payable_for(self, user: User) -> "ExpenseQuerySet":
        if not get_permission_provider().may_pay(user):
            return self.none()
        return (
            self.filter(reimbursement=None)
            .exclude(expensepart__attested_by=None)
            .exclude(confirmed_by=None)
            .order_by("owner__user__username")
        )

    def viewable_by(self, user: User) -> "ExpenseQuerySet":
        provider = get_permission_provider()
        if provider.may_view_all(user):
            return self.all()
        cc_scopes = provider.viewable_cost_centres(user)
        return self.filter(
            Q(expensepart__cost_centre__in=cc_scopes) | Q(owner__user=user)
        ).distinct()


class Expense(models.Model):
    """
    Represents an expense. An expense contains expense parts and information
    about the expense.
    """

    objects = ExpenseQuerySet.as_manager()

    created_date = models.DateField(auto_now_add=True)
    expense_date = models.DateField()
    confirmed_by = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.DO_NOTHING
    )
    confirmed_at = models.DateField(blank=True, null=True, default=None)
    owner = models.ForeignKey(Profile, on_delete=models.DO_NOTHING)
    description = models.TextField()
    reimbursement = models.ForeignKey(
        Payment, blank=True, null=True, on_delete=models.DO_NOTHING
    )
    verification = models.CharField(max_length=7, blank=True)
    is_flagged = models.BooleanField(null=True, blank=True)

    # Returns a string representation of the expense
    def __str__(self):
        return self.description

    # Return the total amount of the expense parts
    def total_amount(self) -> Decimal:
        total = Decimal("0")
        for part in self.parts.all():
            total += part.amount
        return total

    def is_attested(self):
        # Iterates instead of querying so prefetched parts are reused.
        return all(part.attested_by_id is not None for part in self.parts.all())

    def is_paid(self):
        return self.reimbursement_id is not None

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
                description=self.description, kind="expense", id=self.id
            )
            if self.verification:
                try:
                    fortnox_client.retrieve_voucher(
                        settings.FORTNOX_EXPENSE_VOUCHER_SERIES,
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

            # Verify total amount of voucher rows matches the total amount of the expense
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
                    logger.debug(
                        "mismatched total",
                        voucher_total=voucher_total,
                        expense_total=self.total_amount(),
                        voucher_rows=voucher_rows,
                    )
                    raise MismatchedTotalAmountError()

            created = fortnox_client.create_voucher(
                VoucherCreate(
                    Description=description,
                    TransactionDate=self.expense_date.strftime("%Y-%m-%d"),
                    VoucherRows=voucher_rows or [],
                    VoucherSeries=settings.FORTNOX_EXPENSE_VOUCHER_SERIES,
                )
            )
            self.verification = (
                f"{settings.FORTNOX_EXPENSE_VOUCHER_SERIES}{created.VoucherNumber}"
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
        Comment.objects.create(
            author=user.profile,
            expense=self,
            content=f"Bokförde med verifikationsnumret: {self.verification}",
        )
        return self.verification

    def confirm(self, user: User):
        if not user.profile.may_confirm():
            raise UnauthorizedConfirmationError()
        if self.confirmed_by:
            raise DuplicateConfirmationError()
        if self.is_flagged:
            raise FlaggedConfirmationError()
        self.confirmed_by = user
        self.confirmed_at = date.today()

    def unconfirm(self, user: User):
        if not user.profile.may_unconfirm():
            raise UnauthorizedUnconfirmationError()
        if not self.confirmed_by:
            raise NotConfirmedError()
        self.confirmed_by = None
        self.confirmed_at = None

    @staticmethod
    def payable():
        return (
            Expense.objects.filter(reimbursement=None)
            .exclude(expensepart__attested_by=None)
            .exclude(confirmed_by=None)
            .order_by("owner__user__username")
        )


class File(models.Model):
    """
    Represents a file on, for example, S3.
    """

    expense = models.ForeignKey(
        Expense, on_delete=models.CASCADE, null=True, blank=True
    )
    invoice = models.ForeignKey(
        "invoices.Invoice", on_delete=models.CASCADE, null=True, blank=True
    )
    file = models.FileField()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._reset_confirmation()

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        self._reset_confirmation()
        return result

    def _reset_confirmation(self):
        """
        The attached files are part of what a confirmer signs off on, so
        changing them voids an existing confirmation. Note that bulk queryset
        operations bypass this, like all model-level behaviour.
        """
        target = self.expense or self.invoice
        if target is not None and target.confirmed_by_id is not None:
            target.confirmed_by = None
            target.confirmed_at = None
            target.save()

    # Returns a string representation of the file
    def __str__(self):
        return self.file.url


class ExpensePart(models.Model):
    """
    Defines an expense part, which is a specification of a part of an expense.
    """

    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name="parts",
        related_query_name="expensepart",
    )
    cost_centre = models.TextField(blank=True)
    secondary_cost_centre = models.TextField(blank=True)
    budget_line = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    attested_by = models.ForeignKey(
        Profile, blank=True, null=True, on_delete=models.DO_NOTHING
    )
    attest_date = models.DateField(blank=True, null=True)

    # Returns string representation of the model
    def __str__(self):
        return (
            self.expense.__str__()
            + " ("
            + self.budget_line
            + ": "
            + str(self.amount)
            + " kr)"
        )

    def attest(self, user: User):
        if self.expense.is_flagged:
            raise FlaggedAttestationError()
        if self.cost_centre not in user.profile.attestable_cost_centres():
            raise UnauthorizedAttestationError()
        if self.expense.owner == user.profile:
            raise SelfAttestationError()

        self.attested_by = user.profile
        self.attest_date = localdate()
        self.save()
        comment = Comment(
            author=user.profile,
            expense=self.expense,
            content="Attesterar kvittodelen ```" + str(self) + "```",
        )
        comment.save()

    def unattest(self, user):
        self.attested_by = None
        self.attest_date = None

        self.save()

        comment = Comment(
            author=user.profile,
            expense=self.expense,
            content="Avattesterar kvittodelen ```" + str(self) + "```",
        )
        comment.save()


class Comment(models.Model):
    """
    Represents a comment on an expense.
    """

    expense = models.ForeignKey(
        Expense, on_delete=models.CASCADE, null=True, blank=True
    )
    invoice = models.ForeignKey(
        "invoices.Invoice", on_delete=models.CASCADE, null=True, blank=True
    )
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Profile, on_delete=models.DO_NOTHING)
    content = models.TextField()

    # String representation of comment
    def __str__(self):
        return self.author.__str__() + " - " + str(self.date) + ": " + self.content

    class Meta:
        ordering = ["date"]


# Sends mail on comment
# noinspection PyUnusedLocal
@receiver(post_save, sender=Comment)
def send_mail(sender, instance, created, *args, **kwargs):
    from django.conf import settings

    if instance.expense:
        target, kind = instance.expense, "expenses"
    else:
        target, kind = instance.invoice, "invoices"
    owner = target.owner
    if sender == Comment:
        if created and instance.author != owner:
            recipient = owner.user.email
            subject = (
                str(instance.author) + " har lagt till en kommentar på ditt utlägg."
            )
            link = f"{settings.FRONTEND_URL}/{owner.user.username}/{kind}/{target.id}"
            content = render_to_string(
                "email.html", {"comment": instance, "receiver": owner, "link": link}
            )
            email_util.send_mail(recipient, subject, content)
