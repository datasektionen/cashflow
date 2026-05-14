"""Fortnox integration for cashflow.

Layered on top of the pure `fortnox.api_client` subpackage:

- request-scoped API clients (`FortnoxMiddleware`, `FortnoxServiceMiddleware`)
- a `FortnoxRequest` type for view hints
- view decorators (`require_fortnox_service`, `require_fortnox_permission`)
- the `ServiceAccount` Django model storing OAuth tokens
- DRF-flavored domain exceptions raised by the accounting views

Django-dependent names (`ServiceAccount`, `FortnoxRequest`, middleware,
decorators, domain exceptions) are loaded lazily via PEP 562 to avoid
touching the Django app registry while this package is itself being
imported during `apps.populate()`.
"""

import importlib
from typing import TYPE_CHECKING

# Eager: pure api_client surface. No Django dependency, safe to import
# during app loading.
from .api_client import (
    AccessTokenResponse,
    Account,
    AccountNotFound,
    AuthCodeGrant,
    CompanyInformation,
    CostCenter,
    Error,
    Expense,
    FinancialYear,
    FortnoxAPIClient,
    FortnoxAPIError,
    FortnoxAuthenticationError,
    FortnoxDomainError,
    FortnoxInvalidPostData,
    FortnoxMissingFieldsError,
    FortnoxNotFound,
    FortnoxPermissionDenied,
    Me,
    MissingTokenOrSecret,
    NonManualVoucherSeries,
    OpeningQuantity,
    RefreshTokenGrant,
    ResponseParsingError,
    Voucher,
    VoucherCreate,
    VoucherListItem,
    VoucherRow,
    VoucherSeries,
    VoucherSeriesListItem,
)

# Lazy: anything that touches Django models or the app registry. Maps
# the public name to (submodule, attribute) and is resolved on first
# attribute access (PEP 562).
_LAZY_ATTRS: dict[str, tuple[str, str]] = {
    # Django integration
    "FortnoxRequest": ("fortnox.django", "FortnoxRequest"),
    "FortnoxMiddleware": ("fortnox.django", "FortnoxMiddleware"),
    "FortnoxServiceMiddleware": ("fortnox.django", "FortnoxServiceMiddleware"),
    "require_fortnox_service": ("fortnox.django", "require_fortnox_service"),
    "require_fortnox_permission": ("fortnox.django", "require_fortnox_permission"),
    "retrieve_or_refresh_token": ("fortnox.django", "retrieve_or_refresh_token"),
    # Django model
    "ServiceAccount": ("fortnox.models", "ServiceAccount"),
    # Cashflow-specific domain exceptions (DRF-flavored)
    "AlreadyAccountedError": ("fortnox.exceptions", "AlreadyAccountedError"),
    "CashflowVerificationMissingError": ("fortnox.exceptions", "CashflowVerificationMissingError"),
    "FortnoxRecordMissingError": ("fortnox.exceptions", "FortnoxRecordMissingError"),
    "FortnoxServiceNotAvailableError": ("fortnox.exceptions", "FortnoxServiceNotAvailableError"),
}


def __getattr__(name: str):
    target = _LAZY_ATTRS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = target
    value = getattr(importlib.import_module(module_name), attr_name)
    globals()[name] = value  # cache on the module so subsequent access skips __getattr__
    return value


if TYPE_CHECKING:
    # Make the lazy names visible to static type checkers and IDEs.
    from .django import (
        FortnoxMiddleware,
        FortnoxRequest,
        FortnoxServiceMiddleware,
        require_fortnox_permission,
        require_fortnox_service,
        retrieve_or_refresh_token,
    )
    from .exceptions import (
        AlreadyAccountedError,
        CashflowVerificationMissingError,
        FortnoxRecordMissingError,
        FortnoxServiceNotAvailableError,
    )
    from .models import ServiceAccount


__all__ = [
    # === Pure client (re-exported from .api_client) ===
    "FortnoxAPIClient",
    "AuthCodeGrant",
    "RefreshTokenGrant",
    "AccessTokenResponse",
    "Account",
    "CompanyInformation",
    "CostCenter",
    "Expense",
    "FinancialYear",
    "Me",
    "OpeningQuantity",
    "Voucher",
    "VoucherCreate",
    "VoucherListItem",
    "VoucherRow",
    "VoucherSeries",
    "VoucherSeriesListItem",
    "Error",
    "FortnoxAPIError",
    "FortnoxAuthenticationError",
    "FortnoxDomainError",
    "FortnoxInvalidPostData",
    "FortnoxMissingFieldsError",
    "FortnoxNotFound",
    "FortnoxPermissionDenied",
    "AccountNotFound",
    "MissingTokenOrSecret",
    "NonManualVoucherSeries",
    "ResponseParsingError",
    # === Django integration (lazy) ===
    "FortnoxRequest",
    "FortnoxMiddleware",
    "FortnoxServiceMiddleware",
    "require_fortnox_service",
    "require_fortnox_permission",
    "retrieve_or_refresh_token",
    # === Django model (lazy) ===
    "ServiceAccount",
    # === Cashflow-specific domain exceptions (lazy) ===
    "AlreadyAccountedError",
    "CashflowVerificationMissingError",
    "FortnoxRecordMissingError",
    "FortnoxServiceNotAvailableError",
]
