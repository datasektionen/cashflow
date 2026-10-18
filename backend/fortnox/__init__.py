"""Fortnox integration for cashflow.

Layered on top of the pure `fortnox.api_client` subpackage:

- request-scoped API clients (`FortnoxMiddleware`, `FortnoxServiceMiddleware`)
- a `FortnoxRequest` type for view hints
- view decorators (`require_fortnox_service`, `require_fortnox_permission`)
- the `ServiceAccount` Django model storing OAuth tokens
- DRF-flavored domain exceptions raised by the accounting views

Django-dependent names (`ServiceAccount`, `FortnoxRequest`, middleware,
decorators, domain exceptions) are loaded lazily (PEP 810 lazy imports) to avoid
touching the Django app registry while this package is itself being
imported during `apps.populate()`.
"""

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
lazy from .api.problems import (
    AlreadyAccountedProblem,
    CashflowVerificationMissingProblem,
    FortnoxRecordMissingProblem,
    FortnoxServiceNotAvailableProblem,
)

# Lazy: anything that touches Django models or the app registry. Only
# resolved on first use, after app loading has finished.
lazy from .django import (
    FortnoxMiddleware,
    FortnoxRequest,
    FortnoxServiceMiddleware,
    require_fortnox_permission,
    require_fortnox_service,
    retrieve_or_refresh_token,
)
lazy from .models import ServiceAccount

__all__ = [
    "AccessTokenResponse",
    "Account",
    "AccountNotFound",
    # === Cashflow-specific domain exceptions (lazy) ===
    "AlreadyAccountedProblem",
    "AuthCodeGrant",
    "CashflowVerificationMissingProblem",
    "CompanyInformation",
    "CostCenter",
    "Error",
    "Expense",
    "FinancialYear",
    # === Pure client (re-exported from .api_client) ===
    "FortnoxAPIClient",
    "FortnoxAPIError",
    "FortnoxAuthenticationError",
    "FortnoxDomainError",
    "FortnoxInvalidPostData",
    "FortnoxMiddleware",
    "FortnoxMissingFieldsError",
    "FortnoxNotFound",
    "FortnoxPermissionDenied",
    "FortnoxRecordMissingProblem",
    # === Django integration (lazy) ===
    "FortnoxRequest",
    "FortnoxServiceMiddleware",
    "FortnoxServiceNotAvailableProblem",
    "Me",
    "MissingTokenOrSecret",
    "NonManualVoucherSeries",
    "OpeningQuantity",
    "RefreshTokenGrant",
    "ResponseParsingError",
    # === Django model (lazy) ===
    "ServiceAccount",
    "Voucher",
    "VoucherCreate",
    "VoucherListItem",
    "VoucherRow",
    "VoucherSeries",
    "VoucherSeriesListItem",
    "require_fortnox_permission",
    "require_fortnox_service",
    "retrieve_or_refresh_token",
]
