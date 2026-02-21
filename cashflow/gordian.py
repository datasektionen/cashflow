"""This module defines functions to retrieve and parse budget information from the GOrdian API.

https://github.com/datasektionen/gordian
"""
import re
from datetime import timedelta
from typing import Literal, Union, Any, Annotated

from pydantic import BaseModel, Field, TypeAdapter, BeforeValidator
from requests_cache import CachedSession

from expenses.models import ExpensePart
from invoices.models import InvoicePart


# ======================
# Data models
# ======================
class GCostCenter(BaseModel):
    id: int = Field(alias="CostCentreID")
    name: str = Field(alias="CostCentreName")
    type: Literal["committee", "partition", "project", "other"] = Field(alias="CostCentreType")


class GSecondaryCostCenter(BaseModel):
    id: int = Field(alias="SecondaryCostCentreID")
    cc_id: int = Field(alias="CostCentreID")
    name: str = Field(alias="SecondaryCostCentreName")


def validate_account(value: Any) -> list[int]:
    """Ensures the account field is correctly formatted and parses it to a list of account numbers."""
    # In GOrdian the account field can be in the following formats:
    #   (1): 4209            Only one account
    #   (2): 3041, 3042      These specific accounts
    #   (3): 3021-3025       All accounts in the range
    if not isinstance(value, str):
        raise ValueError(f"Expected a string, got {type(value)}")
    try:
        patterns = [r"^\d{4}(, \d{4})*$", r"^\d{4}-\d{4}$", ]
        match _match_regex(value, patterns):
            case r"^\d{4}(, \d{4})*$":  # (1) or (2)
                return [int(a) for a in value.split(",")]
            case r"^\d{4}-\d{4}$":  # (3)
                return list(range(int(value[0:4]), int(value[5:9])))
            case _:
                raise ValueError(f"Unknown error when pattern matching account format")
    except ValueError as e:
        raise ValueError(f"Invalid account format: {value}") from e


class GBudgetLine(BaseModel):
    id: int = Field(alias="BudgetLineID")
    scc_id: int = Field(alias="SecondaryCostCentreID")
    name: str = Field(alias="BudgetLineName")
    account: Annotated[list[int], BeforeValidator(validate_account)] = Field(alias="BudgetLineAccount")
    income: int = Field(alias="BudgetLineIncome")
    expense: int = Field(alias="BudgetLineExpense")
    comment: str = Field(alias="BudgetLineComment")


# Cache Gordian requests for 24 hours
CACHE_SESSION = CachedSession("gordian", expire_after=timedelta(hours=24))

# Type adapters, better for performance to define these once
# These handle parsing list responses from GOrdian
CC_LIST = TypeAdapter(list[GCostCenter])
SCC_LIST = TypeAdapter(list[GSecondaryCostCenter])
BL_LIST = TypeAdapter(list[GBudgetLine])


# ======================
# API request functions
# ======================
def list_cost_centres_from_gordian() -> list[GCostCenter]:
    response = CACHE_SESSION.get(f"https://budget.datasektionen.se/api/CostCentres")
    return CC_LIST.validate_json(response.text)


def list_secondary_cost_centres_from_gordian(cost_center: Union[int, GCostCenter] = None) -> list[GSecondaryCostCenter]:
    if cost_center is not None:
        # Find only secondary cost centres for given cost center
        cc_id = cost_center.id if isinstance(cost_center, GCostCenter) else cost_center
        response = CACHE_SESSION.get("https://budget.datasektionen.se/api/SecondaryCostCentres", params={"id": cc_id})
        secondary_cost_centres = SCC_LIST.validate_json(response.text)
    else:
        # List all cost centers
        cost_centers = list_cost_centres_from_gordian()
        secondary_cost_centres: list[GSecondaryCostCenter] = []
        for cc in cost_centers:
            response = CACHE_SESSION.get("https://budget.datasektionen.se/api/SecondaryCostCentres",
                                         params={"id": cc.id})
            secondary_cost_centres += SCC_LIST.validate_json(response.text)
    return secondary_cost_centres


def list_budget_lines_from_gordian(secondary_cost_center: Union[int, GSecondaryCostCenter]) -> list[GBudgetLine]:
    if secondary_cost_center is not None:
        # Find only budget lines for given secondary cost center
        scc_id = secondary_cost_center.id if isinstance(secondary_cost_center,
                                                        GSecondaryCostCenter) else secondary_cost_center
        response = CACHE_SESSION.get(f"https://budget.datasektionen.se/api/BudgetLines", params={"id": scc_id})
        budget_lines = BL_LIST.validate_json(response.text)
    else:
        # List all budget lines
        secondary_cost_centres = list_secondary_cost_centres_from_gordian()
        budget_lines: list[GBudgetLine] = []
        for scc in secondary_cost_centres:
            response = CACHE_SESSION.get(f"https://budget.datasektionen.se/api/BudgetLines", params={"id": scc.id})
            budget_lines += BL_LIST.validate_json(response.text)
    return budget_lines


def retrieve_account_from_gordian(part: Union[InvoicePart, ExpensePart]) -> list[int]:
    """Retrieves the account number for the budget line for this expense or invoice part"""

    try:
        cost_center = next(cc for cc in list_cost_centres_from_gordian() if cc.name == part.cost_centre)
    except IndexError as e:
        raise ValueError(f"Could not find the cost center `{part.cost_centre}` on GOrdian") from e

    try:
        secondary_cost_center = next(scc for scc in list_secondary_cost_centres_from_gordian(cost_center) if
                                     scc.name == part.secondary_cost_centre)
    except IndexError as e:
        raise ValueError(f"Could not find the secondary cost center `{part.secondary_cost_centre}` on GOrdian`")

    try:
        budget_line = next(
            bl for bl in list_budget_lines_from_gordian(secondary_cost_center) if bl.name == part.budget_line)
    except IndexError as e:
        raise ValueError(f"Could not find the budget line `{part.budget_line}` on GOrdian")

    return budget_line.account


# ======================
# Helper functions
# ======================
def _match_regex(input_str: str, patterns: list[str]) -> str:
    # Tries to match a given string against a list of regex patterns
    # and returns the one that matches, otherwise raises ValueError
    for pattern in patterns:
        if re.match(pattern, input_str):
            return pattern
    raise ValueError(f"{input_str} does not match any of the patterns in {patterns}")
