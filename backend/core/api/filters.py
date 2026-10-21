"""Defines functions for filtering expenses and invoices in list views."""

from datetime import date
from enum import Enum
from typing import Any

from django.contrib.auth.models import User
from django.db.models import Q, Value
from django.db.models.functions import Coalesce
from django.http import QueryDict
from rest_framework import serializers

from core.models import ClaimQuerySet


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
    """Query parameters accepted by the expense/invoice/claim list endpoints."""

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
    reimbursement = serializers.IntegerField(
        required=False, help_text="Filter by reimbursement ID"
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
    REIMBURSEMENT = "reimbursement"


SORT_FIELDS: dict[Sorting, str] = {
    Sorting.ID_DESC: "-id",
    Sorting.CREATED_AT_ASC: "created_date",
    Sorting.CREATED_AT_DESC: "-created_date",
    Sorting.TOTAL_DESC: "-total",
    Sorting.TOTAL_ASC: "total",
}


def _order_by_sorting(queryset: ClaimQuerySet, sorting: Sorting) -> ClaimQuerySet:
    """Orders by the requested field, then descending id so newer rows come
    first among ties and pagination stays stable."""
    match sorting:
        case Sorting.DATE_ASC | Sorting.DATE_DESC:
            expr = Coalesce(
                "expense_data__expense_date",
                "invoice_data__invoice_date",
                Value(date.min),
            )
        case Sorting.TOTAL_ASC | Sorting.TOTAL_DESC:
            expr = Coalesce("total", Value(0))
        case _:
            return queryset.order_by(SORT_FIELDS[sorting], "-id")
    ordering = expr.desc() if sorting.value.startswith("-") else expr.asc()
    return queryset.order_by(ordering, "-id")


def _tristate(
    queryset: ClaimQuerySet, value: Any, condition: Q, *, negate: Q | None = None
) -> ClaimQuerySet:
    """Applies a tristate filter: `condition` for true, `negate` (defaults to
    ~condition) for false, nothing for an absent value."""
    match value:
        case None:
            return queryset
        case "none":
            return queryset.none()
        case False | "false" | "0":
            return queryset.filter(negate if negate is not None else ~condition)
        case _:
            return queryset.filter(condition)


def apply_claim_filters(
    queryset: ClaimQuerySet,
    params: QueryDict | dict[str, Any],
    user: User | None = None,
) -> ClaimQuerySet:
    """Applies filters to a claim queryset based on query parameters.

    Filters that only make sense for one claim type (e.g. confirmed, flagged,
    reimbursement) are expressed per type so they work on mixed querysets.
    """
    query = ClaimQuerySerializer(data=params)
    query.is_valid(raise_exception=True)
    validated = query.validated_data

    is_expense = Q(type="expense")
    is_invoice = Q(type="invoice")

    if claim_type := validated.get(Filter.TYPE):
        queryset = queryset.filter(type=claim_type)
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

    budget_filter = {}
    if name := validated.get(Filter.COST_CENTRE):
        budget_filter["part__cost_centre"] = name
    if name := validated.get(Filter.SECONDARY_COST_CENTRE):
        budget_filter["part__secondary_cost_centre"] = name
    if name := validated.get(Filter.BUDGET_LINE):
        budget_filter["part__budget_line"] = name

    # We need to put all conditions in the same filter to make sure they all apply
    # to the same claim part
    # See https://github.com/datasektionen/cashflow/issues/399
    queryset = queryset.filter(**budget_filter)

    if description := validated.get(Filter.QUERY):
        queryset = queryset.filter(description__icontains=description)

    queryset = _tristate(queryset, validated.get(Filter.ACCOUNTED), ~Q(verification=""))
    queryset = _tristate(
        queryset,
        validated.get(Filter.ATTESTED),
        ~Q(part__attested_by__isnull=True),
        negate=Q(part__attested_by__isnull=True),
    )
    # Invoices are never confirmed, so this filter only narrows down expenses
    queryset = _tristate(
        queryset,
        validated.get(Filter.CONFIRMED),
        is_invoice | (is_expense & Q(expense_data__confirmed_by__isnull=False)),
        negate=is_invoice | (is_expense & Q(expense_data__confirmed_by__isnull=True)),
    )
    queryset = _tristate(
        queryset,
        validated.get(Filter.PAID),
        (is_expense & Q(expense_data__reimbursement__isnull=False))
        | (is_invoice & Q(invoice_data__paid_at__isnull=False)),
        negate=(is_expense & Q(expense_data__reimbursement__isnull=True))
        | (is_invoice & Q(invoice_data__paid_at__isnull=True)),
    )
    # Invoices can never be flagged, so flagged=true excludes them entirely
    queryset = _tristate(
        queryset,
        validated.get(Filter.FLAGGED),
        Q(expense_data__is_flagged=True),
        negate=is_invoice | ~Q(expense_data__is_flagged=True),
    )

    if voucher_series := validated.get(Filter.VOUCHER_SERIES):
        queryset = queryset.filter(verification__startswith=voucher_series)
    if voucher := validated.get(Filter.VOUCHER_NUMBER):
        queryset = queryset.filter(verification__icontains=voucher)
    if reimbursement := validated.get(Filter.REIMBURSEMENT):
        queryset = queryset.filter(expense_data__reimbursement_id=reimbursement)

    return _order_by_sorting(queryset, Sorting(validated["sorting"]))


def apply_expense_filters(
    queryset: ClaimQuerySet,
    params: QueryDict | dict[str, Any],
    user: User | None = None,
) -> ClaimQuerySet:
    return apply_claim_filters(queryset.expenses(), params, user)


def apply_invoice_filters(
    queryset: ClaimQuerySet,
    params: QueryDict | dict[str, Any],
    user: User | None = None,
) -> ClaimQuerySet:
    return apply_claim_filters(queryset.invoices(), params, user)
