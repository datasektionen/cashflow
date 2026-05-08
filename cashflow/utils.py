import hashlib
from typing import Union

import unicodedata
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from structlog import get_logger

from cashflow import dauth
from cashflow import gordian
from cashflow.gordian import GCostCenter
from expenses.models import ExpensePart
from fortnox.api_client.models import CostCenter, Account
from fortnox.django import FortnoxRequest
from invoices.models import InvoicePart

logger = get_logger(__name__)


def has_accounting_permissions(user: User):
    return dauth.has_any_permission_scope("accounting", user)


def may_authenticate_fortnox(user: User):
    return dauth.has_unscoped_permission("manage-fortnox", user)


def build_cache_key(name: str):
    """Creates a cache key that is safe for e.g. memcache

    Normalizes and hashes the input string. For example:

    "My Key" -> "my key" -> "a0e12d601e10154fe574..."
    """
    normalized = unicodedata.normalize("NFKC", name.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def find_cost_center(request: FortnoxRequest, part: Union[InvoicePart, ExpensePart, str],
                     force_refresh: bool = False) -> CostCenter:
    """Finds a cost center on Fortnox that is connected to the given expense or invoice part."""
    query = part if isinstance(part, str) else part.cost_centre

    if not force_refresh:
        cached_cost_center = cache.get(f"fortnox:cost_center:search:by_name:{build_cache_key(query)}", None)
        if cached_cost_center is not None:
            return CostCenter.model_validate(cached_cost_center)
    cost_center = request.fortnox_service.find_cost_center(Description=query)
    cache.set(f"fortnox:cost_center:search:by_name:{build_cache_key(cost_center.Description)}",
              cost_center.model_dump(), timeout=settings.FORTNOX_COST_CENTER_CACHE_TIMEOUT * 60 * 60)
    return cost_center


def list_active_accounts(request: FortnoxRequest, force_refresh: bool = False) -> list[Account]:
    """Lists all active accounts on Fortnox. Caches values for performance"""
    cache_key = "fortnox:accounts:active"
    if not force_refresh:
        cached = cache.get(cache_key)
        if cached is not None:
            return [Account.model_validate(acc) for acc in cached]

    all_accounts = []
    page = 1
    while True:
        page_accounts = request.fortnox_service.list_accounts(limit=500, page=page)
        all_accounts.extend(page_accounts)
        if len(page_accounts) < 500:
            break
        page += 1
    accounts = [acc for acc in all_accounts if acc.Active]

    cache.set(cache_key, [acc.model_dump() for acc in accounts],
        timeout=settings.FORTNOX_ACCOUNT_CACHE_TIMEOUT * 60 * 60, )
    return accounts


def list_active_cost_centers(request: FortnoxRequest, force_refresh: bool = False) -> list[CostCenter]:
    cache_key = "fortnox:costcenters:active"
    if not force_refresh:
        cached = cache.get(cache_key)
        if cached is not None:
            return [CostCenter.model_validate(cc) for cc in cached]

    all_cost_centers = []
    page = 1
    while True:
        page_cost_centers = request.fortnox_service.list_cost_centers(limit=500, page=page)
        all_cost_centers.extend(page_cost_centers)
        if len(page_cost_centers) < 500:
            break
        page += 1
    cost_centers = [cc for cc in all_cost_centers if cc.Active]

    cache.set(cache_key, [cc.model_dump() for cc in cost_centers],
        timeout=settings.FORTNOX_COST_CENTER_CACHE_TIMEOUT * 60, )
    return cost_centers


def retrieve_fortnox_cost_center(request: FortnoxRequest, cost_center: Union[GCostCenter, int]) -> CostCenter:
    """Retrieves the corresponding cost center from Fortnox for this GOrdian cost center"""
    if isinstance(cost_center, int):
        cost_center = gordian.find_cost_center(cc_id=cost_center)
    return request.fortnox_service.find_cost_center(Description=cost_center.name)
