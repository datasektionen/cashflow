"""
This module defines the exceptions used by the Fortnox API client,
handling erroneous requests and responses.
"""

class FortnoxAPIError(Exception):
    pass


class ResponseParsingError(FortnoxAPIError):
    pass