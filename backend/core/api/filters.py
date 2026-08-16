"""Defines functions for filtering expenses and invoices in list views."""

from datetime import date
from enum import Enum
from typing import Any

from django.contrib.auth.models import User
from django.db.models import Value
from django.db.models.functions import Coalesce
from django.http import QueryDict
from rest_framework import serializers

from expenses.models import ExpenseQuerySet
from invoices.models import InvoiceQuerySet


class TristateField(serializers.ChoiceField):

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(choices=["true", "false", "none"], **kwargs)

    def to_internal_value(self, data: Any) -> Any:
        if isinstance(data, bool):
            data = "true" if data else "false"
        return super().to_internal_value(data)


class Sorting(str, Enum):
    ID_DESC = "-id"
    CREATED_AT_ASC = "created_at"
    CREATED_AT_DESC = "-created_at"
    DATE_ASC = "date"
    DATE_DESC = "-date"
    TOTAL_DESC = "-total"
    TOTAL_ASC = "total"


class ClaimQuerySerializer(serializers.Serializer):
    """Query parameters accepted by the expense/invoice/claim list endpoints.

    Also doubles as the OpenAPI schema for those endpoints' query parameters
    (passed directly to `extend_schema(parameters=[...])`).
    """

    user = serializers.CharField(required=False)
    cost_centre = serializers.CharField(required=False)
    secondary_cost_centre = serializers.CharField(required=False)
    budget_line = serializers.CharField(required=False)
    attestable = serializers.BooleanField(required=False)
    confirmable = serializers.BooleanField(required=False)
    accountable = serializers.BooleanField(required=False)
    payable = serializers.BooleanField(required=False)
    type = serializers.ChoiceField(
        choices=["expense", "invoice"],
        required=False,
        help_text="Restrict the claims list to a single type.",
    )
    accounted = TristateField(
        required=False,
        help_text="Whether or not the claim is accounted (has a registered voucher)",
    )
    attested = TristateField(
        required=False,
        help_text="Whether or not every part of the claim has been attested.",
    )
    confirmed = TristateField(
        required=False,
        help_text="Whether or not the claim has been confirmed.",
    )
    paid = TristateField(
        required=False,
        help_text="Whether or not the claim has been paid out.",
    )
    flagged = TristateField(
        required=False,
        help_text="Whether or not this claim is flagged. Expenses only.",
    )
    q = serializers.CharField(
        required=False, help_text="Substring search on the claim's description."
    )
    voucher_series = serializers.CharField(
        max_length=1,
        required=False,
        help_text="Filter by voucher series code, e.g. 'E'",
    )
    voucher_number = serializers.CharField(
        required=False, help_text="Filter by partial voucher number"
    )
    sorting = serializers.ChoiceField(
        choices=[
            Sorting.ID_DESC,
            Sorting.CREATED_AT_ASC,
            Sorting.CREATED_AT_DESC,
            Sorting.DATE_ASC,
            Sorting.DATE_DESC,
            Sorting.TOTAL_DESC,
            Sorting.TOTAL_ASC,
        ],
        required=False,
        default=Sorting.ID_DESC.value,
        help_text="Sort order for the results.",
    )


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
    VOUCHER_SERIES = "voucher_series"
    VOUCHER_NUMBER = "voucher_number"


EXPENSE_SORT_FIELDS: dict[Sorting, str] = {
    Sorting.ID_DESC: "-id",
    Sorting.CREATED_AT_ASC: "created_date",
    Sorting.CREATED_AT_DESC: "-created_date",
    Sorting.DATE_ASC: "expense_date",
    Sorting.DATE_DESC: "-expense_date",
    Sorting.TOTAL_DESC: "-total",
    Sorting.TOTAL_ASC: "total",
}
INVOICE_SORT_FIELDS: dict[Sorting, str] = {
    Sorting.ID_DESC: "-id",
    Sorting.CREATED_AT_ASC: "created_date",
    Sorting.CREATED_AT_DESC: "-created_date",
    Sorting.DATE_ASC: "invoice_date",
    Sorting.DATE_DESC: "-invoice_date",
    Sorting.TOTAL_DESC: "-total",
    Sorting.TOTAL_ASC: "total",
}


def _order_by_sorting(queryset, sorting: Sorting, sort_fields: dict[Sorting, str]):
    """Orders by the requested field, then descending id so newer rows come
    first among ties and pagination stays stable."""
    field = sort_fields[sorting]
    if sorting in (Sorting.DATE_ASC, Sorting.DATE_DESC):
        name = field.lstrip("-")
        expr = Coalesce(name, Value(date.min))
        ordering = expr.desc() if field.startswith("-") else expr.asc()
        return queryset.order_by(ordering, "-id")
    elif sorting in (Sorting.TOTAL_ASC, Sorting.DATE_DESC):
        name = field.lstrip("-")
        expr = Coalesce(name, Value(0))
        ordering = expr.desc() if field.startswith("-") else expr.asc()
        return queryset.order_by(ordering, "-id")
    return queryset.order_by(field, "-id")


def apply_expense_filters(
    queryset: ExpenseQuerySet,
    params: QueryDict | dict[str, Any],
    user: User | None = None,
) -> ExpenseQuerySet:
    """Applies filters to an expense queryset based on query parameters."""
    query = ClaimQuerySerializer(data=params)
    query.is_valid(raise_exception=True)
    validated = query.validated_data

    if username := validated.get(Filter.USER):
        queryset = queryset.filter(owner__user__username=username)
    if user and validated.get(Filter.ATTESTABLE):
        queryset = queryset.attestable_for(user)
    if user and validated.get(Filter.CONFIRMABLE):
        queryset = queryset.confirmable_for(user)
    if user and validated.get(Filter.ACCOUNTABLE):
        queryset = queryset.accountable_for(user)
    if user and validated.get(Filter.PAYABLE):
        queryset = queryset.payable_for(user)
    if name := validated.get(Filter.COST_CENTRE):
        queryset = queryset.filter(expensepart__cost_centre=name)
    if name := validated.get(Filter.SECONDARY_COST_CENTRE):
        queryset = queryset.filter(expensepart__secondary_cost_centre=name)
    if name := validated.get(Filter.BUDGET_LINE):
        queryset = queryset.filter(expensepart__budget_line=name)
    if description := validated.get(Filter.QUERY):
        queryset = queryset.filter(description__icontains=description)
    match validated.get(Filter.ACCOUNTED):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.filter(verification="")
        case _:
            queryset = queryset.exclude(verification="")
    match validated.get(Filter.ATTESTED):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.filter(expensepart__attested_by__isnull=True)
        case _:
            queryset = queryset.exclude(expensepart__attested_by__isnull=True)
    match validated.get(Filter.CONFIRMED):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.filter(confirmed_by__isnull=True)
        case _:
            queryset = queryset.filter(confirmed_by__isnull=False)
    match validated.get(Filter.PAID):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.filter(reimbursement__isnull=True)
        case _:
            queryset = queryset.filter(reimbursement__isnull=False)
    match validated.get(Filter.FLAGGED):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.exclude(is_flagged=True)
        case _:
            queryset = queryset.filter(is_flagged=True)
    if voucher_series := validated.get(Filter.VOUCHER_SERIES):
        queryset = queryset.filter(verification__startswith=voucher_series)
    if voucher := validated.get(Filter.VOUCHER_NUMBER):
        queryset = queryset.filter(verification__icontains=voucher)

    return _order_by_sorting(
        queryset, Sorting(validated["sorting"]), EXPENSE_SORT_FIELDS
    )


def apply_invoice_filters(
    queryset: InvoiceQuerySet,
    params: QueryDict | dict[str, Any],
    user: User | None = None,
) -> InvoiceQuerySet:
    """Applies filters to an invoice queryset based on query parameters."""
    query = ClaimQuerySerializer(data=params)
    query.is_valid(raise_exception=True)
    validated = query.validated_data

    if username := validated.get(Filter.USER):
        queryset = queryset.filter(owner__user__username=username)
    if user and validated.get(Filter.ATTESTABLE):
        queryset = queryset.attestable_for(user)
    if user and validated.get(Filter.CONFIRMABLE):
        queryset = queryset.confirmable_for(user)
    if user and validated.get(Filter.ACCOUNTABLE):
        queryset = queryset.accountable_for(user)
    if user and validated.get(Filter.PAYABLE):
        queryset = queryset.payable_for(user)
    if name := validated.get(Filter.COST_CENTRE):
        queryset = queryset.filter(invoicepart__cost_centre=name)
    if name := validated.get(Filter.SECONDARY_COST_CENTRE):
        queryset = queryset.filter(invoicepart__secondary_cost_centre=name)
    if name := validated.get(Filter.BUDGET_LINE):
        queryset = queryset.filter(invoicepart__budget_line=name)
    if description := validated.get(Filter.QUERY):
        queryset = queryset.filter(description__icontains=description)
    match validated.get(Filter.ACCOUNTED):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.filter(verification="")
        case _:
            queryset = queryset.exclude(verification="")
    match validated.get(Filter.ATTESTED):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.filter(invoicepart__attested_by__isnull=True)
        case _:
            queryset = queryset.exclude(invoicepart__attested_by__isnull=True)
    match validated.get(Filter.CONFIRMED):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.filter(confirmed_by__isnull=True)
        case _:
            queryset = queryset.filter(confirmed_by__isnull=False)
    match validated.get(Filter.PAID):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            queryset = queryset.filter(payed_at__isnull=True)
        case _:
            queryset = queryset.filter(payed_at__isnull=False)
    # Invoices can never be flagged, so a request for flagged=true (or the
    # nonsensical "none") should exclude them entirely rather than silently
    # ignoring the filter and returning every invoice.
    match validated.get(Filter.FLAGGED):
        case None:
            pass
        case "none":
            queryset = queryset.none()
        case False | "false" | "0":
            pass
        case _:
            queryset = queryset.none()
    if voucher_series := validated.get(Filter.VOUCHER_SERIES):
        queryset = queryset.filter(verification__startswith=voucher_series)
    if voucher := validated.get(Filter.VOUCHER_NUMBER):
        queryset = queryset.filter(verification__icontains=voucher)

    return _order_by_sorting(
        queryset, Sorting(validated["sorting"]), INVOICE_SORT_FIELDS
    )
