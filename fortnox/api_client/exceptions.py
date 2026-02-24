"""
This module defines the exceptions used by the Fortnox API client,
handling erroneous requests and responses.
"""
from enum import Enum
from types import MappingProxyType


class FortnoxAPIError(Exception):
    pass


# ======================
# Authentication/permissions
# ======================

class FortnoxAuthenticationError(FortnoxAPIError):
    pass


class MissingTokenOrSecret(FortnoxAPIError):
    pass


class FortnoxPermissionDenied(FortnoxAPIError):
    pass


# ======================
# Not found errors
# ======================

class FortnoxNotFound(FortnoxAPIError):
    pass


class AccountNotFound(FortnoxAPIError):
    pass


# ======================
# Domain error (business rule related)
# ======================

class FortnoxDomainError(FortnoxAPIError):
    pass


class NonManualVoucherSeries(FortnoxAPIError):
    pass


# ======================
# Invalid requests
# ======================

class FortnoxInvalidPostData(FortnoxAPIError):
    pass


class FortnoxMissingFieldsError(FortnoxAPIError):
    pass


# ======================
# Misc.
# ======================

class ResponseParsingError(FortnoxAPIError):
    pass


# ======================
# Fortnox error codes and exception mapping
# ======================

class FortnoxErrorCode(int, Enum):
    """Represents the error codes that can be included in Fortnox ErrorInformation responses"""
    RESOURCE_NOT_FOUND = 2000423
    PERMISSION_DENIED = 2000663
    MISSING_TOKEN_OR_SECRET = 2000311
    INVALID_FIELD_TYPE = 2001392
    MISSING_FIELDS = 2001795
    INVALID_VOUCHER_SERIES = 2001939
    INVALID_ACCOUNT = 2001798
    NON_MANUAL_VOUCHER_SERIES = 2001940


CODE_EXCEPTION_MAPPING = MappingProxyType(
    {FortnoxErrorCode.RESOURCE_NOT_FOUND: FortnoxNotFound, FortnoxErrorCode.PERMISSION_DENIED: FortnoxPermissionDenied,
     FortnoxErrorCode.MISSING_TOKEN_OR_SECRET: MissingTokenOrSecret,
     FortnoxErrorCode.INVALID_FIELD_TYPE: FortnoxInvalidPostData,
     FortnoxErrorCode.MISSING_FIELDS: FortnoxMissingFieldsError,
     FortnoxErrorCode.INVALID_VOUCHER_SERIES: FortnoxInvalidPostData, FortnoxErrorCode.INVALID_ACCOUNT: AccountNotFound,
     FortnoxErrorCode.NON_MANUAL_VOUCHER_SERIES: NonManualVoucherSeries, })
"""Maps error codes to suitable exception classes, read only."""
