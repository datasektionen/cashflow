"""This module defines functions to retrieve and parse budget information from the GOrdian API.

https://github.com/datasektionen/gordian
"""
import logging
import re
from typing import Literal, Union, Any, Annotated
from warnings import deprecated

import requests
from django.conf import settings
from django.core.cache import cache
from pydantic import BaseModel, Field, TypeAdapter, BeforeValidator

from expenses.models import ExpensePart
from invoices.models import InvoicePart


logger = logging.getLogger(__name__)


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
    #   (4): (empty)         No accounts
    if isinstance(value, list):
        return [int(x) for x in value]
    elif not isinstance(value, str):
        raise ValueError(f"Expected a list of ints or a string, got {type(value)}")
    try:
        patterns = [r"^\d{4}(, \d{4})*$", r"^\d{4}-\d{4}$", r"^$"]
        try:
            match _match_regex(value, patterns):
                case r"^\d{4}(, \d{4})*$":  # (1) or (2)
                    return [int(a) for a in value.split(",")]
                case r"^\d{4}-\d{4}$":  # (3)
                    return list(range(int(value[0:4]), int(value[5:9])))
                case r"^$":  # (4)
                    return []
                case _:
                    raise ValueError(
                        f"Unknown error when pattern matching account format")  # TODO: Temporary fix for erronous accounts on GOrdian
        except ValueError:
            return []
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


# Type adapters, better for performance to define these once
# These handle parsing list responses from GOrdian
CC_LIST = TypeAdapter(list[GCostCenter])
SCC_LIST = TypeAdapter(list[GSecondaryCostCenter])
BL_LIST = TypeAdapter(list[GBudgetLine])

# Caching
# These determine which key is used to look up all stored cost center etc. IDs currently in the cache
COST_CENTER_SEARCH_KEYS = "gordian:cost_center:search_keys"
SND_COST_CENTER_SEARCH_KEYS = "gordian:secondary_cost_center:search_keys"
BUDGET_LINE_SEARCH_KEYS = "gordian:budget_line:search_keys"


# ======================
# API request functions
# ======================
@deprecated("This function is meant to be used temporarily, until a better solution is found")
def find_cost_center(cc_id: int = None, name: str = None, force_refresh=False) -> GCostCenter:
    """Finds a cost center on GOrdian based on the given fields"""
    from .utils import build_cache_key

    if not force_refresh:
        if cc_id is not None:
            cost_center = cache.get(f"gordian:cost_center:{cc_id}", None)
            if cost_center is not None:
                return GCostCenter.model_validate(cost_center, by_name=True)

    all_cost_centers = list_cost_centres_from_gordian(force_refresh=force_refresh)
    if cc_id is not None:
        try:
            cost_center = GCostCenter.model_validate(next(cc for cc in all_cost_centers if cc.id == cc_id))
        except StopIteration as e:
            raise ValueError(f"Couldn't find cost center with {cc_id=}") from e

        return cost_center
    elif name is not None:
        cost_center = cache.get(f"gordian:cost_center:search:name:{build_cache_key(name)}", None)
        if cost_center is not None:
            logger.debug("Cache hit for cost center with name %s", name)
            return GCostCenter.model_validate(cost_center, by_name=True)
        try:
            cost_center = next(cc for cc in all_cost_centers if cc.name == name)
            cache.set(f"gordian:cost_center:search:name:{build_cache_key(cost_center.name)}", cost_center.model_dump(),
                      timeout=settings.GORDIAN_COST_CENTER_CACHE_TIMEOUT * 60 * 60)
        except StopIteration as e:
            raise ValueError(f"Couldn't find cost center with {name=}") from e
        return GCostCenter.model_validate(cost_center)
    else:
        raise ValueError(f"You must specify either a cost center ID or name")


@deprecated("This function is meant to be used temporarily, until a better solution is found")
def find_snd_cost_center(scc_id: int = None, name: str = None, force_refresh=False) -> GSecondaryCostCenter:
    """Finds a secondary cost center on GOrdian based on the given fields"""
    from .utils import build_cache_key

    if not force_refresh:
        if scc_id is not None:
            secondary_cost_center = cache.get(f"gordian:secondary_cost_center:{scc_id}", None)
            if secondary_cost_center is not None:
                return GSecondaryCostCenter.model_validate(secondary_cost_center)

    all_snd_cost_centers = list_secondary_cost_centres_from_gordian(force_refresh=force_refresh)
    if scc_id is not None:
        try:
            secondary_cost_center = next(scc for scc in all_snd_cost_centers if scc.id == scc_id)
        except StopIteration as e:
            raise ValueError(f"Couldn't find cost secondary center with {scc_id=}") from e
        return GSecondaryCostCenter.model_validate(secondary_cost_center)
    elif name is not None:
        secondary_cost_center = cache.get(f"gordian:secondary_cost_center:search:name:{build_cache_key(name)}", None)
        if secondary_cost_center is not None:
            logger.debug("Cache hit for secondary cost center with name %s", name)
            return GSecondaryCostCenter.model_validate(secondary_cost_center, by_name=True)
        try:
            secondary_cost_center = next(scc for scc in all_snd_cost_centers if scc.name == name)
            cache.set(f"gordian:secondary_cost_center:search:name:{build_cache_key(secondary_cost_center.name)}", secondary_cost_center.model_dump(),
                      timeout=settings.GORDIAN_COST_CENTER_CACHE_TIMEOUT * 60 * 60)
        except StopIteration as e:
            raise ValueError(f"Couldn't find secondary cost center with {name=}") from e
        return GSecondaryCostCenter.model_validate(secondary_cost_center)
    else:
        raise ValueError(f"You must specify either a secondary cost center ID or name")


@deprecated("This function is meant to be used temporarily, until a better solution is found")
def find_budget_line(bl_id: int = None, name: str = None, force_refresh=False) -> GBudgetLine:
    """Finds a budget line on GOrdian based on the given fields"""
    from .utils import build_cache_key

    if not force_refresh:
        if bl_id is not None:
            budget_line = cache.get(f"gordian:budget_line:{bl_id}", None)
            if budget_line is not None:
                return GBudgetLine.model_validate(budget_line)

    all_budget_lines = list_budget_lines_from_gordian(force_refresh=force_refresh)
    if bl_id is not None:
        try:
            budget_line = next(bl for bl in all_budget_lines if bl.id == bl_id)
        except StopIteration as e:
            raise ValueError(f"Couldn't find cost budget line with {bl_id=}") from e
        return GBudgetLine.model_validate(budget_line)
    elif name is not None:
        budget_line = cache.get(f"gordian:budget_line:search:name:{build_cache_key(name)}", None)
        if budget_line is not None:
            logger.debug("Cache hit for budget line with name %s", name)
            return GBudgetLine.model_validate(budget_line, by_name=True)
        try:
            budget_line = next(bl for bl in all_budget_lines if bl.name == name)
            cache.set(f"gordian:budget_line:search:name:{build_cache_key(budget_line.name)}", budget_line.model_dump(),
                      timeout=settings.GORDIAN_COST_CENTER_CACHE_TIMEOUT * 60 * 60)
        except StopIteration as e:
            raise ValueError(f"Couldn't find budget line with {name=}") from e
        return GBudgetLine.model_validate(budget_line)
    else:
        raise ValueError(f"You must specify either a budget line ID or name")


def list_cost_centres_from_gordian(force_refresh: bool = False) -> list[GCostCenter]:
    """Lists all cost centers on GOrdian.

    Caches responses by default, the timeout is configurable using GORDIAN_COST_CENTER_CACHE_TIMEOUT.
    :param force_refresh: Forces fetching from the API, bypassing the cache
    :return: A list of cost centers using the GCostCenter data-class.
    """

    if not force_refresh:
        keys = cache.get(COST_CENTER_SEARCH_KEYS, [])
        cost_centers = CC_LIST.validate_python(cache.get_many(keys).values(), by_name=True)
        if len(cost_centers) != 0:
            return cost_centers

    response = requests.get(f"https://budget.datasektionen.se/api/CostCentres")
    cost_centers = CC_LIST.validate_json(response.text)
    cache.set(COST_CENTER_SEARCH_KEYS, [_cost_center_key(cc) for cc in cost_centers],
              timeout=settings.GORDIAN_COST_CENTER_CACHE_TIMEOUT * 60 * 60)
    cache.set_many({_cost_center_key(cc): cc.model_dump() for cc in cost_centers},
                   timeout=settings.GORDIAN_COST_CENTER_CACHE_TIMEOUT * 60 * 60)
    return cost_centers


def list_secondary_cost_centres_from_gordian(cost_center: Union[int, GCostCenter] = None,
                                             force_refresh: bool = False) -> list[GSecondaryCostCenter]:
    cc_id = cost_center.id if isinstance(cost_center, GCostCenter) else cost_center

    if not force_refresh:
        keys = cache.get(SND_COST_CENTER_SEARCH_KEYS, None)
        if keys is None and cost_center is not None:
            keys = cache.get(f"{SND_COST_CENTER_SEARCH_KEYS}:{cc_id}", None)
        if keys is not None:
            secondary_cost_centers = SCC_LIST.validate_python(cache.get_many(keys).values(), by_name=True)
            if cost_center is not None:
                return [scc for scc in secondary_cost_centers if scc.cc_id == cc_id]
            return secondary_cost_centers

    if cost_center is not None:
        response = requests.get(f"https://budget.datasektionen.se/api/SecondaryCostCentres", params={"id": cc_id})
        secondary_cost_centers = SCC_LIST.validate_json(response.text)

        # (!) We don't want to overwrite the existing search keys -> store cc specific keys separately
        cache.set(f"{SND_COST_CENTER_SEARCH_KEYS}:{cc_id}",
                  [_snd_cost_center_key(scc) for scc in secondary_cost_centers],
                  timeout=settings.GORDIAN_COST_CENTER_CACHE_TIMEOUT * 60 * 60)
        cache.set_many({_snd_cost_center_key(scc): scc.model_dump() for scc in secondary_cost_centers},
                       timeout=settings.GORDIAN_COST_CENTER_CACHE_TIMEOUT * 60 * 60)

    else:
        # List all secondary cost centers
        cost_centers = list_cost_centres_from_gordian(force_refresh=force_refresh)

        secondary_cost_centers = []
        for cc in cost_centers:
            response = requests.get(f"https://budget.datasektionen.se/api/SecondaryCostCentres", params={"id": cc.id})
            secondary_cost_centers += SCC_LIST.validate_json(response.text)

        cache.set(SND_COST_CENTER_SEARCH_KEYS, [_snd_cost_center_key(scc) for scc in secondary_cost_centers],
                  timeout=settings.GORDIAN_COST_CENTER_CACHE_TIMEOUT * 60 * 60)
        cache.set_many({_snd_cost_center_key(scc): scc.model_dump() for scc in secondary_cost_centers},
                       timeout=settings.GORDIAN_COST_CENTER_CACHE_TIMEOUT * 60 * 60)

    return secondary_cost_centers


def list_budget_lines_from_gordian(secondary_cost_center: Union[int, GSecondaryCostCenter] = None,
                                   force_refresh: bool = False) -> list[GBudgetLine]:
    scc_id = secondary_cost_center.id if isinstance(secondary_cost_center,
                                                    GSecondaryCostCenter) else secondary_cost_center
    if not force_refresh:

        keys = cache.get(BUDGET_LINE_SEARCH_KEYS, None)
        if keys is None and secondary_cost_center is not None:
            keys = cache.get(f"{BUDGET_LINE_SEARCH_KEYS}:{scc_id}", None)
        if keys is not None:
            budget_lines = BL_LIST.validate_python(cache.get_many(keys).values(), by_name=True)
            if secondary_cost_center is not None:
                return [bl for bl in budget_lines if bl.scc_id == scc_id]
            return budget_lines

    if secondary_cost_center is not None:
        response = requests.get(f"https://budget.datasektionen.se/api/BudgetLines", params={"id": scc_id})
        budget_lines = BL_LIST.validate_json(response.text)

        cache.set(f"{BUDGET_LINE_SEARCH_KEYS}:{scc_id}", [_budget_line_key(bl) for bl in budget_lines],
                  timeout=settings.GORDIAN_COST_CENTER_CACHE_TIMEOUT * 60 * 60)
        cache.set_many({_budget_line_key(bl): bl.model_dump() for bl in budget_lines},
                       timeout=settings.GORDIAN_COST_CENTER_CACHE_TIMEOUT * 60 * 60)

    else:
        # Retrieve all budget lines (from all secondary cost centers)
        secondary_cost_centers = list_secondary_cost_centres_from_gordian(force_refresh=force_refresh)
        budget_lines = []
        for scc in secondary_cost_centers:
            response = requests.get(f"https://budget.datasektionen.se/api/BudgetLines", params={"id": scc.id})
            if response.text.strip() == "null":  # No budget lines for this scc
                continue
            budget_lines += BL_LIST.validate_json(response.text)

        cache.set(BUDGET_LINE_SEARCH_KEYS, [_budget_line_key(bl) for bl in budget_lines],
                  timeout=settings.GORDIAN_COST_CENTER_CACHE_TIMEOUT * 60 * 60)
        cache.set_many({_budget_line_key(bl): bl.model_dump() for bl in budget_lines},
                       timeout=settings.GORDIAN_COST_CENTER_CACHE_TIMEOUT * 60 * 60)

    return budget_lines


def retrieve_account_from_gordian(part: Union[InvoicePart, ExpensePart]) -> list[int]:
    """Retrieves the account number for the budget line for this expense or invoice part"""

    try:
        cost_center = next(cc for cc in list_cost_centres_from_gordian() if cc.name == part.cost_centre)
    except StopIteration as e:
        raise ValueError(f"Could not find the cost center `{part.cost_centre}` on GOrdian") from e

    try:
        secondary_cost_center = next(scc for scc in list_secondary_cost_centres_from_gordian(cost_center) if
                                     scc.name == part.secondary_cost_centre)
    except StopIteration as e:
        raise ValueError(
            f"Could not find the secondary cost center `{cost_center.name}/{part.secondary_cost_centre}` on GOrdian`") from e

    try:
        budget_line = next(
            bl for bl in list_budget_lines_from_gordian(secondary_cost_center) if bl.name == part.budget_line)
    except StopIteration as e:
        raise ValueError(
            f"Could not find the budget line `{cost_center.name}/{secondary_cost_center.name}/{part.budget_line}` on GOrdian") from e

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


def _cost_center_key(cost_center: GCostCenter) -> str:
    # Formatted cache key for cost centers
    return f"gordian:cost_center:{cost_center.id}"


def _snd_cost_center_key(snd_cost_center: GSecondaryCostCenter) -> str:
    # Formatted cache key for secondary cost centers
    return f"gordian:secondary_cost_center:{snd_cost_center.id}"


def _budget_line_key(budget_line: GBudgetLine) -> str:
    # Formatted cache key for budget lines
    return f"gordian:budget_line:{budget_line.id}"
