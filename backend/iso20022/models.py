from collections import defaultdict

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models, transaction
from django.utils import timezone
from pydantic import TypeAdapter
from typing import TYPE_CHECKING

from core.exceptions import MissingBankInfoError, ZeroSumReimbursementError
from iso20022.handelsbanken import LocalAccountPayment, SE_IBAN, HandelsbankenISO20022

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from expenses.models import Expense, Profile, Payment


class PaymentInitiationFile(models.Model):
    """Represents a payment initiation file (pain.001) for making payments from the bank.

    A pain.001 file follows the ISO 20022 standard and is an XML document specifying one or more payments. One file
    can contain several transactions, which means one file can be used to create payments to multiple users and expenses.
    """

    file = models.FileField()
    msg_id = models.CharField(max_length=35)

    @classmethod
    def create_batch_reimbursement(cls, expenses: list[Expense], payer: User):
        """Create a payment initiation file for a batch reimbursement of expenses."""
        from expenses.models import Payment

        TypeAdapter(SE_IBAN).validate_python(settings.ORG_IBAN)

        # We want one transaction per user
        by_owner: dict[Profile, list[Expense]] = defaultdict(list)
        for expense in expenses:
            by_owner[expense.owner].append(expense)

        payments = []

        with transaction.atomic():
            for owner in by_owner.keys():

                # Resolve bank details
                if not owner.has_bank_info:
                    raise MissingBankInfoError()

                # Get sum of user's expenses
                amount = sum(expense.total_amount() for expense in by_owner[owner])
                if amount == 0:
                    raise ZeroSumReimbursementError()

                reimbursement = Payment.objects.create(
                    payer=payer.profile, receiver=owner
                )
                for expense in by_owner[owner]:
                    expense.reimbursement = reimbursement
                    expense.save(update_fields=["reimbursement"])

                payment = LocalAccountPayment(
                    debtor_iban=settings.ORG_IBAN,
                    creditor_iban=owner.get_iban(),
                    creditor_message=f"{settings.PAYMENT_TAG_PREFIX}{reimbursement.id}",
                    date=timezone.now().date(),
                    instr_id=f"{settings.PAYMENT_TAG_PREFIX}{reimbursement.id}",
                    end_to_end_id=f"{settings.PAYMENT_TAG_PREFIX}{reimbursement.id}",
                    amount=amount,
                )
                payments.append(payment)

            # Create the ISO 20022 file
            now = timezone.now()
            msg_id = f"{settings.PAYMENT_TAG_PREFIX}{now:%Y%m%d%H%M%S}"
            pmt_inf_id = msg_id
            xml_str = HandelsbankenISO20022.local_account_payment(
                payments, settings.ORG_IBAN, msg_id, pmt_inf_id
            )

            file = SimpleUploadedFile(
                content=xml_str.encode("utf-8"),
                content_type="text/xml",
                name=msg_id,
            )

            return PaymentInitiationFile.objects.create(
                file=file,
                msg_id=msg_id,
            )
