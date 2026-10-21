# This file mostly tests the constraints etc on the models


import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from core.models import *
from expenses.models import ExpenseData
from invoices.models import InvoiceData


@pytest.mark.django_db
def test_claim_only_expense_or_invoice(user):
    owner = Profile.objects.create(user=user)
    expense_data = ExpenseData.objects.create(expense_date=timezone.localdate())
    invoice_data = InvoiceData.objects.create(
        invoice_date=timezone.localdate(),
        invoice_number="1",
        due_date=timezone.localdate(),
    )

    # Neither
    with pytest.raises(IntegrityError), transaction.atomic():
        Claim.objects.create(owner=owner, description="ABC")

    # Both
    with pytest.raises(IntegrityError), transaction.atomic():
        Claim.objects.create(
            owner=user.core_profile,
            description="ABC",
            expense_data=expense_data,
            invoice_data=invoice_data,
        )

    # Exactly one
    Claim.objects.create(owner=owner, description="ABC", expense_data=expense_data)
    Claim.objects.create(owner=owner, description="ABC", invoice_data=invoice_data)


@pytest.mark.django_db
def test_claim_type_generated_correctly(user):
    owner = Profile.objects.create(user=user)
    expense_data = ExpenseData.objects.create(expense_date=timezone.localdate())
    invoice_data = InvoiceData.objects.create(
        invoice_date=timezone.localdate(),
        invoice_number="1",
        due_date=timezone.localdate(),
    )

    expense = Claim.objects.create(
        owner=owner, description="My expense", expense_data=expense_data
    )
    invoice = Claim.objects.create(
        owner=owner, description="My invoice", invoice_data=invoice_data
    )

    assert expense.type == "expense"
    assert invoice.type == "invoice"
