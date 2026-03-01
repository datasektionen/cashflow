import hashlib
import unicodedata
from typing import Union

from django.conf import settings
from django.core.cache import cache

from expenses.models import ExpensePart
from fortnox.api_client.models import CostCenter, Account
from fortnox.django import FortnoxRequest
from invoices.models import InvoicePart


def build_cache_key(name: str):
    """Creates a cache key that is safe for e.g. memcache

    Normalizes and hashes the input string. For example:

    "My Key" -> "my key" -> "a0e12d601e10154fe574..."
    """
    normalized = unicodedata.normalize("NFKC", name.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def find_cost_center(request: FortnoxRequest, part: Union[InvoicePart, ExpensePart],
                     force_refresh: bool = False) -> CostCenter:
    """Finds a cost center on Fortnox that is connected to the given expense or invoice part."""
    if not force_refresh:
        cached_cost_center = cache.get(f"fortnox:cost_center:search:by_name:{build_cache_key(part.cost_centre)}", None)
        if cached_cost_center is not None:
            return CostCenter.model_validate(cached_cost_center)
    cost_center = request.fortnox.find_cost_center(Description=part.cost_centre)
    cache.set(f"fortnox:cost_center:search:by_name:{build_cache_key(cost_center.Description)}",
              cost_center.model_dump(), timeout=settings.FORTNOX_COST_CENTER_CACHE_TIMEOUT * 60 * 60)
    return cost_center


def list_active_accounts(request: FortnoxRequest, force_refresh: bool = False) -> list[Account]:
    """Lists all active accounts on Fortnox. Caches values for performance"""

    if not force_refresh:

        keys = cache.get("fortnox:account:search_keys", [])
        if len(keys) != 0:
            cached_accounts = cache.get_many(keys)
            return [Account.model_validate(acc) for acc in cached_accounts.values()]
    # Retrieve from fortnox
    accounts = [acc for acc in request.fortnox.list_accounts() if acc.Active]
    cache.set_many({f"fortnox:account:{acc.Number}": acc.model_dump() for acc in accounts},
                   timeout=settings.FORTNOX_COST_CENTER_CACHE_TIMEOUT * 60 * 60)
    cache.set("fortnox:account:search_keys", [f"fortnox:account:{acc.Number}" for acc in accounts],
              timeout=settings.FORTNOX_ACCOUNT_CACHE_TIMEOUT * 60 * 60)
    return accounts
