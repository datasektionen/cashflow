from django_filters import rest_framework as filters

from core.api.filters import ClaimFilter, ClaimOrdering
from core.models import Claim


class ExpenseOrdering(ClaimOrdering):
    ordering_fields = (
        *ClaimOrdering.ordering_fields,
        ("expense_data__id", "id"),
        ("expense_data__expense_date", "expense_date"),
        ("expense_data__confirmed_at", "confirmed_at"),
        ("expense_data__is_flagged", "is_flagged"),
        ("expense_data__reimbursement", "reimbursement"),
    )


class ExpenseFilter(ClaimFilter):
    expense_date = filters.DateFromToRangeFilter(
        field_name="expense_data__expense_date"
    )
    confirmed_at = filters.DateFromToRangeFilter(
        field_name="expense_data__confirmed_at"
    )
    reimbursement = filters.NumberFilter(field_name="expense_data__reimbursement")
    confirmed_by = filters.CharFilter(field_name="expense_data__confirmed_by__username")

    sorting = ExpenseOrdering()

    class Meta:
        model = Claim
        fields = (
            *ClaimFilter.Meta.fields,
            "expense_date",
            "reimbursement",
            "confirmed_by",
            # "ordering",
            "sorting",
        )
