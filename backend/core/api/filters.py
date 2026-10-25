"""Defines functions for filtering expenses and invoices in list views."""

from typing import ClassVar

from django.db.models import F, Q
from django_filters import rest_framework as filters

from core.models import Claim
from core.search import claim_search


class ClaimOrdering(filters.OrderingFilter):
    ordering_fields: ClassVar[tuple[tuple[str, str], ...]] = (
        ("date", "date"),
        ("total", "total"),
        ("description", "description"),
        ("type", "type"),
        ("created_date", "created_date"),
        ("owner__user__username", "user"),
        ("expense_data__is_flagged", "is_flagged"),
        ("part__cost_centre", "cost_centre"),
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("fields", self.ordering_fields)
        super().__init__(*args, **kwargs)

    def get_ordering_value(self, param):  # pyright: ignore[reportIncompatibleMethodOverride]
        # Put null values last
        descending = param.startswith("-")
        field = F(self.param_map.get(param.lstrip("-"), param.lstrip("-")))  # pyright: ignore[reportOptionalMemberAccess]
        if descending:
            return field.desc(nulls_last=True)
        return field.asc(nulls_last=True)


class ClaimFilter(filters.FilterSet):
    # Meta
    user = filters.CharFilter(field_name="owner__user__username")
    type = filters.MultipleChoiceFilter(
        field_name="type", choices=(("expense", "expense"), ("invoice", "invoice"))
    )
    date = filters.DateFromToRangeFilter(field_name="date")

    # Budget
    cost_centre = filters.CharFilter(field_name="part__cost_centre")
    secondary_cost_centre = filters.CharFilter(field_name="part__secondary_cost_centre")
    budget_line = filters.CharFilter(field_name="part__budget_line")

    # Available actions
    attestable = filters.BooleanFilter(method="filter_attestable")
    confirmable = filters.BooleanFilter(method="filter_confirmable")
    accountable = filters.BooleanFilter(method="filter_accountable")
    payable = filters.BooleanFilter(method="filter_payable")

    # Status
    attested = filters.BooleanFilter(method="filter_attested")
    confirmed = filters.BooleanFilter(method="filter_confirmed")
    accounted = filters.BooleanFilter(method="filter_accounted")
    paid = filters.BooleanFilter(method="filter_paid")
    flagged = filters.BooleanFilter(method="filter_flagged")

    # Accounting
    verification = filters.CharFilter(
        field_name="verification", lookup_expr="icontains"
    )
    voucher_series = filters.CharFilter(method="filter_voucher_series")

    # Sorting
    sorting = ClaimOrdering()

    # Search
    q = filters.CharFilter(method="filter_description_fuzzy")

    class Meta:
        model = Claim
        fields = (
            "user",
            "cost_centre",
            "secondary_cost_centre",
            "budget_line",
            "date",
            "attestable",
            "confirmable",
            "accountable",
            "payable",
            "attested",
            "accounted",
            "paid",
            "flagged",
        )

    def filter_attestable(self, qs, name, value):
        if self.request:
            return qs.attestable_for(self.request.user) if value else qs
        else:
            return qs.none()

    def filter_confirmable(self, qs, name, value):
        if self.request:
            return qs.confirmable_for(self.request.user) if value else qs
        else:
            return qs.none()

    def filter_accountable(self, qs, name, value):
        if self.request:
            return qs.accountable_for(self.request.user) if value else qs
        else:
            return qs.none()

    def filter_payable(self, qs, name, value):
        if self.request:
            return qs.payable_for(self.request.user) if value else qs
        else:
            return qs.none()

    def filter_attested(self, qs, name, value):
        return qs.filter(part__attested_by__isnull=not value)

    def filter_confirmed(self, qs, name, value):
        return qs.filter(
            ~Q(expense_data__confirmed_by__isnull=value) | Q(type="invoice")
        )

    def filter_accounted(self, qs, name, value):
        return qs.exclude(verification="") if value else qs.filter(verification="")

    def filter_paid(self, qs, name, value):
        return qs.filter(
            (Q(type="expense") & Q(expense_data__reimbursement_id__isnull=not value))
            | (Q(type="invoice") & Q(invoice_data__paid_at__isnull=not value))
        )

    def filter_flagged(self, qs, name, value):
        if value:
            return qs.filter(type="expense", expense_data__is_flagged=True)
        else:
            return qs.filter(
                Q(type="expense", expense_data__is_flagged=False) | Q(type="invoice")
            )

    def filter_description_fuzzy(self, qs, name, value):
        return claim_search(qs, description_fuzzy=value)

    def filter_voucher_series(self, qs, name, value):
        return qs.filter(verification__startswith=value)
