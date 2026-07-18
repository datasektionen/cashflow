"""Pure, framework-agnostic Fortnox API client.

This subpackage has no Django dependency and could be lifted into a
standalone library. See the parent `fortnox` package for the Django
integration (middleware, decorators, ServiceAccount model).
"""

from .client import FortnoxAPIClient
from .exceptions import (
    AccountNotFound,
    FortnoxAPIError,
    FortnoxAuthenticationError,
    FortnoxDomainError,
    FortnoxInvalidPostData,
    FortnoxMissingFieldsError,
    FortnoxNotFound,
    FortnoxPermissionDenied,
    MissingTokenOrSecret,
    NonManualVoucherSeries,
    ResponseParsingError,
)
from .models import (
    AccessTokenResponse,
    Account,
    AuthCodeGrant,
    CompanyInformation,
    CostCenter,
    Error,
    Expense,
    FinancialYear,
    Me,
    OpeningQuantity,
    RefreshTokenGrant,
    Voucher,
    VoucherCreate,
    VoucherListItem,
    VoucherRow,
    VoucherSeries,
    VoucherSeriesListItem,
)

__all__ = [
    # Client
    "FortnoxAPIClient",
    # Grants & auth response
    "AuthCodeGrant",
    "RefreshTokenGrant",
    "AccessTokenResponse",
    # Domain models
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
    # Error envelope
    "Error",
    # Exceptions
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
]
