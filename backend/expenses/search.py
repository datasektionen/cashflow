from django.db.models import QuerySet
from typing import TypedDict, Unpack, Optional

from core.api.filters import apply_expense_filters
from core.search import fuzzy_model_search
from expenses.models import Expense, ExpenseQuerySet


class ExpenseSearchFields(TypedDict):
    description: Optional[str]
    description_fuzzy: Optional[str]


def expense_search(
    queryset: ExpenseQuerySet[Expense], **search_fields: Unpack[ExpenseSearchFields]
) -> QuerySet[Expense]:

    filtered: QuerySet[Expense] = apply_expense_filters(
        queryset, dict(search_fields), user=None
    )

    for key, value in search_fields.items():
        match key, value:
            case "description", str():
                filtered = filtered.filter(description__icontains=value)
            case "description_fuzzy", str():
                return fuzzy_model_search(filtered, value, "description")

    return filtered
