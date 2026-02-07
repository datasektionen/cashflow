"""
This module defines the exceptions used by the Fortnox API client,
handling erroneous requests and responses.
"""


class FortnoxAPIError(Exception):
    pass


class FortnoxAuthenticationError(FortnoxAPIError):
    pass


class FortnoxPermissionDenied(FortnoxAPIError):
    pass


class FortnoxNotFound(FortnoxAPIError):
    pass


class FortnoxInvalidPostData(FortnoxAPIError):
    pass


class FortnoxMissingFieldsError(FortnoxAPIError):
    pass


class ResponseParsingError(FortnoxAPIError):
    pass
