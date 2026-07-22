from typing import Any

from django.http import QueryDict
from enum import Enum
from pydantic import BaseModel


class BudgetFilter(Enum):
    ACTIVE = ("active", str)
    COST_CENTRE = ("cost_centre", int)
    SECONDARY_COST_CENTRE = ("secondary_cost_centre", int)


class _CostCentre(BaseModel):
    id: int | None
    name: str
    type: str | None
    active: bool


def check_filter_type(filter: BudgetFilter, value: Any) -> None:
    if not isinstance(value, filter.value[1]):
        raise ValueError(
            f"Unexpected value for budget filter {filter.name}: {value.__class__.__name__}"
        )


def _apply_active_filter(items: list[dict], params: QueryDict) -> list[dict]:
    if active := params.get(BudgetFilter.ACTIVE.value[0]):
        check_filter_type(BudgetFilter.ACTIVE, active)
        items = [item for item in items if item["active"]]

    return items


def apply_cost_centre_filter(ccs: list[dict], params: QueryDict) -> list[dict]:
    return _apply_active_filter(ccs, params)


def apply_secondary_cost_centre_filter(
    sccs: list[dict], params: QueryDict
) -> list[dict]:
    if cc := params.get(BudgetFilter.COST_CENTRE.value[0]):
        try:
            cc_id = int(cc)
        except ValueError:
            raise ValueError(
                f"Unexpected value for budget filter {BudgetFilter.COST_CENTRE.name}: {cc!r}"
            )
        sccs = [item for item in sccs if item["cc_id"] == cc_id]
    return _apply_active_filter(sccs, params)


def apply_budget_line_filter(bls: list[dict], params: QueryDict) -> list[dict]:

    if scc := params.get(BudgetFilter.SECONDARY_COST_CENTRE.value[0]):
        try:
            scc_id = int(scc)
        except ValueError:
            raise ValueError(
                f"Unexpected value for budget filter {BudgetFilter.SECONDARY_COST_CENTRE.name}: {scc!r}"
            )
        bls = [item for item in bls if item["scc_id"] == scc_id]

    return _apply_active_filter(bls, params)
