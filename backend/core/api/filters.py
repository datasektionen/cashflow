"""Defines functions for filtering expenses and invoices in list views."""

from typing import Any

from django.db.models import QuerySet
from enum import Enum

from django.contrib.auth.models import User
from django.http import QueryDict
from drf_spectacular.utils import OpenApiParameter

from expenses.models import Expense, ExpenseQuerySet
from invoices.models import Invoice, InvoiceQuerySet


class Filter(str, Enum):
    USER = "user"
    COST_CENTRE = "cost_centre"
    SECONDARY_COST_CENTRE = "secondary_cost_centre"
    BUDGET_LINE = "budget_line"
    ATTESTABLE = "attestable"
    CONFIRMABLE = "confirmable"
    ACCOUNTABLE = "accountable"
    PAYABLE = "payable"
    TYPE = "type"
    ACCOUNTED = "accounted"
    ATTESTED = "attested"
    QUERY = "q"
    FLAGGED = "flagged"
    CONFIRMED = "confirmed"
    PAID = "paid"


# For use in extend_schema() to generate OpenAPI documentation
OPENAPI_PARAMS: dict[Filter, OpenApiParameter] = {
    Filter.USER: OpenApiParameter(
        Filter.USER.value,
        type=int,
        required=False,
    ),
    Filter.COST_CENTRE: OpenApiParameter(
        Filter.COST_CENTRE.value,
        type=str,
        required=False,
    ),
    Filter.SECONDARY_COST_CENTRE: OpenApiParameter(
        Filter.SECONDARY_COST_CENTRE.value,
        type=str,
        required=False,
    ),
    Filter.BUDGET_LINE: OpenApiParameter(
        Filter.BUDGET_LINE.value,
        type=str,
        required=False,
    ),
    Filter.ATTESTABLE: OpenApiParameter(
        Filter.ATTESTABLE.value,
        type=bool,
        required=False,
    ),
    Filter.CONFIRMABLE: OpenApiParameter(
        Filter.CONFIRMABLE.value,
        type=bool,
        required=False,
    ),
    Filter.ACCOUNTABLE: OpenApiParameter(
        Filter.ACCOUNTABLE.value,
        type=bool,
        required=False,
    ),
    Filter.PAYABLE: OpenApiParameter(
        Filter.PAYABLE.value,
        type=bool,
        required=False,
    ),
    Filter.TYPE: OpenApiParameter(
        Filter.TYPE.value,
        type=str,
        required=False,
        enum=["expense", "invoice"],
        description="Restrict the claims list to a single type.",
    ),
    Filter.ACCOUNTED: OpenApiParameter(
        Filter.ACCOUNTED.value,
        type=bool,
        required=False,
        description="Whether or not the claim is accounted (has a registered voucher)",
    ),
    Filter.ATTESTED: OpenApiParameter(
        Filter.ATTESTED.value,
        type=bool,
        required=False,
        description="Whether or not every part of the claim has been attested.",
    ),
    Filter.QUERY: OpenApiParameter(
        Filter.QUERY.value,
        type=str,
        required=False,
        description="Substring search on the claim's description.",
    ),
    Filter.FLAGGED: OpenApiParameter(
        Filter.FLAGGED.value,
        type=bool,
        required=False,
        description="Whether or not this claim is flagged. Expenses only.",
    ),
    Filter.CONFIRMED: OpenApiParameter(
        Filter.CONFIRMED.value,
        type=bool,
        required=False,
        description="Whether or not the claim has been confirmed.",
    ),
    Filter.PAID: OpenApiParameter(
        Filter.PAID.value,
        type=bool,
        required=False,
        description="Whether or not the claim has been paid out.",
    ),
}


def apply_expense_filters(
    queryset: ExpenseQuerySet[Expense],
    params: QueryDict | dict[str, Any],
    user: User | None = None,
) -> QuerySet[Expense]:
    """Applies filters to an expense queryset based on query parameters."""
    if username := params.get(Filter.USER):
        queryset = queryset.filter(owner__user__username=username)
    if user and params.get(Filter.ATTESTABLE):
        queryset = queryset.attestable_for(user)
    if user and params.get(Filter.CONFIRMABLE):
        queryset = queryset.confirmable_for(user)
    if user and params.get(Filter.ACCOUNTABLE):
        queryset = queryset.accountable_for(user)
    if user and params.get(Filter.PAYABLE):
        queryset = queryset.payable_for(user)
    if name := params.get(Filter.COST_CENTRE):
        queryset = queryset.filter(expensepart__cost_centre=name)
    if name := params.get(Filter.SECONDARY_COST_CENTRE):
        queryset = queryset.filter(expensepart__secondary_cost_centre=name)
    if name := params.get(Filter.BUDGET_LINE):
        queryset = queryset.filter(expensepart__budget_line=name)
    if query := params.get(Filter.QUERY):
        queryset = queryset.filter(description__icontains=query)
    match params.get(Filter.ACCOUNTED):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.filter(verification="")
        case _:
            queryset = queryset.exclude(verification="")
    match params.get(Filter.ATTESTED):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.filter(expensepart__attested_by__isnull=True)
        case _:
            queryset = queryset.exclude(expensepart__attested_by__isnull=True)
    match params.get(Filter.CONFIRMED):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.filter(confirmed_by__isnull=True)
        case _:
            queryset = queryset.filter(confirmed_by__isnull=False)
    match params.get(Filter.PAID):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.filter(reimbursement__isnull=True)
        case _:
            queryset = queryset.filter(reimbursement__isnull=False)
    match params.get(Filter.FLAGGED):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.exclude(is_flagged=True)
        case _:
            queryset = queryset.filter(is_flagged=True)
    return queryset


def apply_invoice_filters(
    queryset: InvoiceQuerySet[Invoice],
    params: QueryDict | dict[str, Any],
    user: User | None = None,
) -> QuerySet[Invoice]:
    """Applies filters to an invoice queryset based on query parameters."""
    if username := params.get(Filter.USER):
        queryset = queryset.filter(owner__user__username=username)
    if user and params.get(Filter.ATTESTABLE):
        queryset = queryset.attestable_for(user)
    if user and params.get(Filter.CONFIRMABLE):
        queryset = queryset.confirmable_for(user)
    if user and params.get(Filter.ACCOUNTABLE):
        queryset = queryset.accountable_for(user)
    if user and params.get(Filter.PAYABLE):
        queryset = queryset.payable_for(user)
    if name := params.get(Filter.COST_CENTRE):
        queryset = queryset.filter(invoicepart__cost_centre=name)
    if name := params.get(Filter.SECONDARY_COST_CENTRE):
        queryset = queryset.filter(invoicepart__secondary_cost_centre=name)
    if name := params.get(Filter.BUDGET_LINE):
        queryset = queryset.filter(invoicepart__budget_line=name)
    if query := params.get(Filter.QUERY):
        queryset = queryset.filter(description__icontains=query)
    match params.get(Filter.ACCOUNTED):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.filter(verification="")
        case _:
            queryset = queryset.exclude(verification="")
    match params.get(Filter.ATTESTED):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.filter(invoicepart__attested_by__isnull=True)
        case _:
            queryset = queryset.exclude(invoicepart__attested_by__isnull=True)
    match params.get(Filter.CONFIRMED):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.filter(confirmed_by__isnull=True)
        case _:
            queryset = queryset.filter(confirmed_by__isnull=False)
    match params.get(Filter.PAID):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.filter(payed_at__isnull=True)
        case _:
            queryset = queryset.filter(payed_at__isnull=False)
    return queryset
