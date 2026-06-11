import re
from datetime import date
from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.db import models

if TYPE_CHECKING:
    from fortnox.api_client import FortnoxAPIClient
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.template.loader import render_to_string
from django.utils.timezone import localdate
from cashflow import email_util
from core.permissions import get_permission_provider
from core.exceptions import (
    UnauthorizedAttestationError,
    SelfAttestationError,
    UnauthorizedConfirmationError,
    DuplicateConfirmationError,
    FlaggedConfirmationError,
    UnauthorizedAccountingError,
    AlreadyAccountedError,
    FortnoxRecordMissingError,
    CashflowVerificationMissingError,
)


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

    # Return a string representation of the user
    def __str__(self):
        return self.user.first_name + " " + self.user.last_name

    # Creates a dict from the model
    def to_dict(self):
        person_dict = model_to_dict(self)
        person_dict["username"] = self.user.username
        person_dict["first_name"] = self.user.first_name
        person_dict["last_name"] = self.user.last_name
        person_dict["bank_info"]["bank_account"] = self.bank_account
        person_dict["bank_info"]["sorting_number"] = self.sorting_number
        person_dict["bank_info"]["bank_name"] = self.bank_name
        del person_dict["user"]
        del person_dict["id"]
        return person_dict

    # Creates and returns an object with the user's properties
    def user_dict(self):
        return {
            "id": self.user.id,
            "username": self.user.username,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": self.user.email,
            "bank_info": {
                "bank_account": self.bank_account,
                "sorting_number": self.sorting_number,
                "bank_name": self.bank_name,
            },
        }

    def may_view_all(self):
        return get_permission_provider().may_view_all(self.user)

    def may_view_all_payments(self):
        return get_permission_provider().may_view_all_payments(self.user)

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

    # Return a unicode representation of the payment
    def __unicode__(self):
        return f"Payment #{self.id} on {self.date} to {self.receiver}"

    # Return a dict from the model
    def to_dict(self):
        payment = model_to_dict(self)
        payment["payer"] = self.payer.user_dict()
        payment["receiver"] = self.receiver.user_dict()
        payment["tag"] = self.tag()
        payment["amount"] = self.amount()
        return payment

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
        qs = self.filter(expensepart__attested_by__isnull=True).exclude(is_flagged=True)
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

    # Returns a unicode representation of the expense
    def __unicode__(self):
        return self.description

    # Returns a json dict from the expense
    def __repr__(self):
        return str(self.to_dict())

    def status(self):
        if self.verification:
            return "Bokförd som " + str(self.verification)
        if self.reimbursement:
            return "Utbetald"
        if self.is_attested() and self.confirmed_by:
            return "Inväntar utbetalning"
        if self.is_attested() and not self.confirmed_by:
            return "Attesterad men inte bekräftad av kassör"
        if not self.is_attested() and self.confirmed_by:
            return "Inte attesterad men bekräftad av kassör"
        return "Inte attesterad"

    # Return the total amount of the expense parts
    def total_amount(self):
        total = 0
        for part in self.parts.all():
            total += part.amount
        return total

    # Returns the cost_centres belonging to the expense as a list [{ cost_centres: 'Name' }, ...]
    def cost_centres(self):
        return self.parts.order_by("cost_centre").values("cost_centre").distinct()

    def is_attested(self):
        return self.parts.filter(attested_by__isnull=True).count() == 0

    def is_paid(self):
        return self.reimbursement is not None

    # Returns a dict representation of the model
    def to_dict(self):
        exp = model_to_dict(self)
        exp["created_date"] = self.created_date
        exp["expense_parts"] = [
            part.to_dict() for part in ExpensePart.objects.filter(expense=self)
        ]
        exp["owner_username"] = self.owner.user.username
        exp["owner_first_name"] = self.owner.user.first_name
        exp["owner_last_name"] = self.owner.user.last_name
        exp["amount"] = self.total_amount()
        exp["cost_centres"] = [
            cost_centre["cost_centre"] for cost_centre in self.cost_centres()
        ]
        exp["status"] = self.status()
        exp["is_flagged"] = self.is_flagged
        if self.reimbursement is not None:
            exp["reimbursement"] = self.reimbursement.to_dict()
        return exp

    @staticmethod
    def confirmable():
        return (
            Expense.objects.filter(confirmed_by__isnull=True)
            .exclude(is_flagged=True)
            .distinct()
        )

    def account(
        self,
        user: User,
        fortnox_client: "FortnoxAPIClient | None" = None,
        part_accounts: "dict[int, tuple[int, str]] | None" = None,
        voucher_number: str | None = None,
    ):
        if not get_permission_provider().may_account(user, self):
            raise UnauthorizedAccountingError()

        if fortnox_client is not None:
            from django.conf import settings
            from fortnox import FortnoxNotFound
            from fortnox.api_client.models import VoucherCreate, VoucherRow

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

            voucher_rows = [
                VoucherRow(
                    Account=settings.FORTNOX_EXPENSE_CREDIT_ACCOUNT,
                    Credit=float(self.total_amount()),
                )
            ]
            if part_accounts:
                for part in self.parts.all():
                    acct, cc = part_accounts[part.id]
                    voucher_rows.append(
                        VoucherRow(
                            Account=acct, CostCenter=cc, Debit=float(part.amount)
                        )
                    )

            created = fortnox_client.create_voucher(
                VoucherCreate(
                    Description=description,
                    TransactionDate=self.expense_date.strftime("%Y-%m-%d"),
                    VoucherRows=voucher_rows,
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

        if self.verification:
            self.save()
            Comment.objects.create(
                author=user.profile,
                expense=self,
                content=f"Bokförde med verifikationsnumret: {self.verification}",
            )

    def confirm(self, user: User):
        if not user.profile.may_confirm():
            raise UnauthorizedConfirmationError()
        if self.confirmed_by:
            raise DuplicateConfirmationError()
        if self.is_flagged:
            raise FlaggedConfirmationError()
        self.confirmed_by = user
        self.confirmed_at = date.today()

    @staticmethod
    def payable():
        return (
            Expense.objects.filter(reimbursement=None)
            .exclude(expensepart__attested_by=None)
            .exclude(confirmed_by=None)
            .order_by("owner__user__username")
        )


FILE_REGEX = re.compile(r".*\.(jpg|jpeg|png|gif|bmp)", re.IGNORECASE)


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

    # Returns a string representation of the file
    def __str__(self):
        return self.file.url

    # Returns a unicode representation of the file
    def __unicode__(self):
        return self.file.url

    # Returns a dict representation of the file
    def to_dict(self):
        return {"url": self.file.url, "id": self.id}

    # Returns true if image url ends with commit image file names
    def is_image(self):
        return FILE_REGEX.match(self.file.name)

    def is_pdf(self):
        return self.file.name.lower().endswith(".pdf")


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

    # Returns unicode representation of the model
    def __unicode__(self):
        return (
            self.expense.__unicode__()
            + " ("
            + self.budget_line
            + ": "
            + str(self.amount)
            + " kr)"
        )

    def attest(self, user: User):

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

    # Returns dict representation of the model
    def to_dict(self):
        exp_part = model_to_dict(self)
        del exp_part["expense"]
        if self.attested_by is not None:
            exp_part["attested_by_username"] = self.attested_by.user.username
            exp_part["attested_by_first_name"] = self.attested_by.user.first_name
            exp_part["attested_by_last_name"] = self.attested_by.user.last_name
        return exp_part


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

    # Unicode representation of comment
    def __unicode__(self):
        return self.author.__unicode__() + " - " + str(self.date) + ": " + self.content

    # Dict representation of the comment
    def to_dict(self):
        comment = model_to_dict(self)
        comment["author_username"] = self.author.user.username
        comment["author_first_name"] = self.author.user.first_name
        comment["author_last_name"] = self.author.user.last_name
        return comment

    class Meta:
        ordering = ["date"]


# Sends mail on comment
# noinspection PyUnusedLocal
@receiver(post_save, sender=Comment)
def send_mail(sender, instance, created, *args, **kwargs):
    owner = instance.expense.owner if instance.expense else instance.invoice.owner
    if sender == Comment:
        if created and instance.author != owner:
            recipient = owner.user.email
            subject = (
                str(instance.author) + " har lagt till en kommentar på ditt utlägg."
            )
            content = render_to_string(
                "email.html", {"comment": instance, "receiver": owner}
            )
            email_util.send_mail(recipient, subject, content)
