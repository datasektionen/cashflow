from drf_problems.utils import register_exception
from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidInvoiceDateError(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "The provided invoice date is invalid. It cannot be in the future."
    default_code = "invalid_invoice_date"
    title = "Invalid invoice date"


class InvalidDueDateError(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "The provided due date is invalid. It must be in the future."
    default_code = "invalid_due_date"
    title = "Invalid due date"


class VerificationRequiredError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "For an accounted invoice you must provide a voucher/verification code."
    )
    default_code = "invoice_verification_required"
    title = "Missing verification code"


register_exception(InvalidInvoiceDateError)
register_exception(InvalidDueDateError)
register_exception(VerificationRequiredError)
