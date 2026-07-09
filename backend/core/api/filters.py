"""Defines functions for filtering expenses and invoices in list views."""

from enum import Enum

from django.contrib.auth.models import User
from django.http import QueryDict
from drf_spectacular.utils import OpenApiParameter

from expenses.models import ExpenseQuerySet
from invoices.models import InvoiceQuerySet


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
}


def apply_expense_filters(
    queryset: ExpenseQuerySet, params: QueryDict, user: User | None = None
) -> ExpenseQuerySet:
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
    if accounted := params.get(Filter.ACCOUNTED):
        if accounted:
            queryset = queryset.exclude(verification="")
        elif not accounted:
            queryset = queryset.filter(verification="")
    return queryset


def apply_invoice_filters(
    queryset: InvoiceQuerySet, params: QueryDict, user: User | None = None
) -> InvoiceQuerySet:
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
    if accounted := params.get(Filter.ACCOUNTED):
        if accounted:
            queryset = queryset.exclude(verification="")
        elif not accounted:
            queryset = queryset.filter(verification="")
    return queryset
