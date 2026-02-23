"""
This module defines the exceptions used by the Fortnox API client,
handling erroneous requests and responses.
"""


class FortnoxAPIError(Exception):
    pass


# ======================
# Authentication/permissions
# ======================

class FortnoxAuthenticationError(FortnoxAPIError):
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
