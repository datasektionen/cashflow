from drf_problems.utils import register_exception
from rest_framework import status
from rest_framework.exceptions import APIException


class InvoiceFileRequiredError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "At least one image or PDF file is required to create an invoice."
    default_code = "invoice_file_required"
    title = "Missing file for creating an invoice"


class InvoicePartInvalidJSONError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid JSON format for invoice parts."
    default_code = "invoice_part_invalid_json"
    title = "Invalid JSON for invoice parts"


class InvoicePartRequiredError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "At least one invoice part is required."
    default_code = "invoice_part_required"
    title = "Missing invoice part"


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


class InvalidDateFormatError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The provided date is malformed. Dates should be given as plain strings in the following format: YYYY-MM-DD"
    default_code = "invalid_date_format"
    title = "Invalid date format"


class VerificationRequiredError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "For an accounted invoice you must provide a voucher/verification code."
    )
    default_code = "invoice_verification_required"
    title = "Missing verification code"


register_exception(InvoiceFileRequiredError)
register_exception(InvoicePartInvalidJSONError)
register_exception(InvalidInvoiceDateError)
register_exception(InvalidDueDateError)
register_exception(InvalidDateFormatError)
register_exception(VerificationRequiredError)
