import hashlib
from datetime import datetime, date
from decimal import Decimal

import unicodedata
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from rapidfuzz import process
from structlog import get_logger

from cashflow import dauth
from cashflow import gordian
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


def list_active_accounts(
    request: FortnoxRequest, force_refresh: bool = False
) -> list[Account]:
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

    cache.set(
        cache_key,
        [acc.model_dump() for acc in accounts],
        timeout=settings.FORTNOX_ACCOUNT_CACHE_TIMEOUT * 60 * 60,
    )
    return accounts


def list_active_cost_centers(
    request: FortnoxRequest, force_refresh: bool = False
) -> list[CostCenter]:
    cache_key = "fortnox:costcenters:active"
    if not force_refresh:
        cached = cache.get(cache_key)
        if cached is not None:
            return [CostCenter.model_validate(cc) for cc in cached]

    all_cost_centers = []
    page = 1
    while True:
        page_cost_centers = request.fortnox_service.list_cost_centers(
            limit=500, page=page
        )
        all_cost_centers.extend(page_cost_centers)
        if len(page_cost_centers) < 500:
            break
        page += 1
    cost_centers = [cc for cc in all_cost_centers if cc.Active]

    cache.set(
        cache_key,
        [cc.model_dump() for cc in cost_centers],
        timeout=settings.FORTNOX_COST_CENTER_CACHE_TIMEOUT * 60,
    )
    return cost_centers


def fortnox_account_for_part(request: FortnoxRequest, part) -> Account | None:
    """Retrieves the Fortnox account that the part should be accounted on, based on GOrdian."""
    active_accounts = list_active_accounts(request)
    account_by_number = {a.Number: a for a in active_accounts}

    try:
        number = gordian.retrieve_account_from_gordian(part)[0]
    except IndexError:
        logger.error(
            "failed to resolve account from gordian",
            part=part,
            cost_center=part.cost_centre,
            secondary_cost_center=part.secondary_cost_centre,
            budget_line=part.budget_line,
        )
        return None
    account = account_by_number.get(number)
    if account is None:
        logger.error(
            "account number from gordian not found in fortnox active accounts",
            account_number=number,
            cost_center=part.cost_centre,
            secondary_cost_center=part.secondary_cost_centre,
            budget_line=part.budget_line,
        )
        return None
    logger.debug("resolved account number", account_number=account.Number)
    return account


def fortnox_cost_center_for_part(
    request: FortnoxRequest, part: ExpensePart | InvoicePart
) -> Account | None:
    """Retrieves the Fortnox cost center that the part should be accounted in, based on Gordian."""
    cost_centers = list_active_cost_centers(request)
    cost_center_by_description = {cc.Description: cc for cc in cost_centers}
    cost_center = cost_center_by_description.get(part.cost_centre, None)
    if not cost_center:
        # Fuzzy search
        # Some cost centers are composed as "Cost center - Secondary" in Fortnox
        query, score_cutoff = (f"{part.cost_centre} - {part.secondary_cost_centre}", 90)
        description, score, _ = process.extractOne(
            query, [cc.Description for cc in cost_centers]
        )
        if score >= score_cutoff:
            logger.debug(
                "fuzzy match on cost center",
                query=query,
                match=description,
                score=score,
                score_cutoff=score_cutoff,
            )
            cost_center = cost_center_by_description.get(description, None)
        else:
            logger.error(
                "unable to resolve cost center fuzzily",
                cost_center=part.cost_centre,
                secondary_cost_center=part.secondary_cost_centre,
                budget_line=part.budget_line,
                query=query,
                closest_match=description,
                score=score,
                score_cutoff=score_cutoff,
            )

    return cost_center


# Hack to properly serialize Decimal as a number in json without losing precision
class FakeFloat(float):
    def __init__(self, value):
        self._value = value

    def __repr__(self):
        return str(self._value)


def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return FakeFloat(obj)
    raise TypeError("Type %s not serializable" % type(obj))
