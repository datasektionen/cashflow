from django_filters import rest_framework as filters

from core.api.filters import ClaimFilter, ClaimOrdering
from core.models import Claim


class InvoiceOrdering(ClaimOrdering):
    ordering_fields = (
        *ClaimOrdering.ordering_fields,
        ("invoice_data__id", "id"),
        ("invoice_data__invoice_date", "invoice_date"),
        ("invoice_data__invoice_number", "invoice_number"),
        ("invoice_data__due_date", "due_date"),
        ("invoice_data__paid_at", "paid_at"),
        ("invoice_data__paid_by", "paid_by"),
    )


class InvoiceFilter(ClaimFilter):
    invoice_date = filters.DateFromToRangeFilter(
        field_name="invoice_data__invoice_date"
    )
    due_date = filters.DateFromToRangeFilter(field_name="invoice_data__due_date")
    paid_at = filters.DateFromToRangeFilter(field_name="invoice_data__paid_at")
    paid_by = filters.CharFilter(field_name="invoice_data__paid_by__user__username")

    invoice_number = filters.CharFilter(
        field_name="invoice_data__invoice_number", lookup_expr="icontains"
    )

    sorting = InvoiceOrdering()

    class Meta:
        model = Claim
        fields = (*ClaimFilter.Meta.fields, "invoice_date")
