"""API exceptions that are shared between other applications.

E.g. errors that can occur both for claims and invoices.
"""

from drf_problems.utils import register_exception
from rest_framework import status
from rest_framework.exceptions import APIException


class PartInvalidJSONError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid JSON format for expense or invoice parts."
    default_code = "part_invalid_json"
    title = "Invalid JSON for expense or invoice parts"


class FileRequiredError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "At least one image or PDF file is required to create an expense or invoice."
    )
    default_code = "file_required"
    title = "Missing file for expense or invoice"


class InvalidDateFormatError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A provided date is malformed. Dates should be given as plain strings in the following format: YYYY-MM-DD"
    default_code = "invalid_date_format"
    title = "Invalid date format"


register_exception(PartInvalidJSONError)
register_exception(FileRequiredError)
register_exception(InvalidDateFormatError)


class PartRequiredError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "At least one part is required to create an expense or invoice."
    default_code = "part_required"
    title = "Missing expense or invoice parts"


register_exception(PartRequiredError)


class AttestationPermissionDenied(APIException):
    status_code = 403
    title = "Attestation permission denied"
    default_detail = (
        "You do not have permission to attest this expense or invoice part."
    )
    default_code = "attestation_permission_denied"


register_exception(AttestationPermissionDenied)
