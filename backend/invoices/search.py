from django.db.models import QuerySet
from typing import TypedDict, Unpack, Optional

from core.api.filters import apply_invoice_filters
from core.search import fuzzy_model_search
from invoices.models import Invoice, InvoiceQuerySet


class InvoiceSearchFields(TypedDict):
    description: Optional[str]
    description_fuzzy: Optional[str]


def invoice_search(
    queryset: InvoiceQuerySet[Invoice], **search_fields: Unpack[InvoiceSearchFields]
) -> QuerySet[Invoice]:

    filtered: QuerySet[Invoice] = apply_invoice_filters(
        queryset, dict(search_fields), user=None
    )

    for key, value in search_fields.items():
        match key, value:
            case "description", str():
                filtered = filtered.filter(description__icontains=value)
            case "description_fuzzy", str():
                return fuzzy_model_search(filtered, value, "description")

    return filtered
