from drf_problems.utils import register_exception
from rest_framework import status
from rest_framework.exceptions import APIException


class PartInvalidJSONProblem(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid JSON format for expense or invoice parts."
    default_code = "part_invalid_json"
    title = "Invalid JSON for expense or invoice parts"


class FileRequiredProblem(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "At least one image or PDF file is required to create an expense or invoice."
    )
    default_code = "file_required"
    title = "Missing file for expense or invoice"


class InvalidDateFormatProblem(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A provided date is malformed. Dates should be given as plain strings in the following format: YYYY-MM-DD"
    default_code = "invalid_date_format"
    title = "Invalid date format"


register_exception(PartInvalidJSONProblem)
register_exception(FileRequiredProblem)
register_exception(InvalidDateFormatProblem)


class PartRequiredProblem(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "At least one part is required to create an expense or invoice."
    default_code = "part_required"
    title = "Missing expense or invoice parts"


register_exception(PartRequiredProblem)


class AttestationPermissionDeniedProblem(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    title = "Attestation permission denied"
    default_detail = (
        "You do not have permission to attest this expense or invoice part."
    )
    default_code = "attestation_permission_denied"


register_exception(AttestationPermissionDeniedProblem)


class AlreadyAttestedProblem(APIException):
    status_code = status.HTTP_409_CONFLICT
    title = "Resource already attested"
    default_detail = "This expense or invoice part is already attested"
    default_code = "already_attested"


class EmptyCommentProblem(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "A comment cannot be blank or consist only of whitespace."
    default_code = "empty_comment"
    title = "Empty comment"


register_exception(EmptyCommentProblem)


class ConfirmationPermissionDeniedProblem(APIException):
    status_code = 403
    title = "Confirmation permission denied"
    default_detail = "You do not have permission to confirm this expense or invoice."
    default_code = "confirmation_permission_denied"


register_exception(ConfirmationPermissionDeniedProblem)


class AlreadyConfirmedProblem(APIException):
    status_code = status.HTTP_409_CONFLICT
    title = "Resource already confirmed"
    default_detail = "This expense or invoice is already confirmed"
    default_code = "already_confirmed"


register_exception(AlreadyConfirmedProblem)


class NotConfirmableProblem(APIException):
    status_code = status.HTTP_409_CONFLICT
    title = "Resource cannot be confirmed"
    default_detail = "This expense or invoice cannot be confirmed."
    default_code = "not_confirmable"


register_exception(NotConfirmableProblem)


class IsFlaggedProblem(APIException):
    status_code = status.HTTP_409_CONFLICT
    title = "Resource is flagged"
    default_detail = "This expense or invoice is flagged and cannot be confirmed."
    default_code = "resource_is_flagged"


register_exception(IsFlaggedProblem)


class UnconfirmationPermissionDeniedProblem(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    title = "Unconfirmation permission denied"
    default_detail = "You do not have permission to unconfirm this expense or invoice."
    default_code = "unconfirmation_permission_denied"


register_exception(UnconfirmationPermissionDeniedProblem)


class NotConfirmedProblem(APIException):
    status_code = status.HTTP_409_CONFLICT
    title = "Resource is not confirmed"
    default_detail = "This expense or invoice is not confirmed."
    default_code = "not_confirmed"


register_exception(NotConfirmedProblem)


class FlagPermissionDeniedProblem(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    title = "Flag permission denied"
    default_detail = "You do not have permission to flag this expense."
    default_code = "flag_permission_denied"


register_exception(FlagPermissionDeniedProblem)


class AccountingPermissionDeniedProblem(APIException):
    status_code = 403
    default_code = "accounting_permission_denied"
    title = "Permission denied for accounting expense/invoice"
    default_detail = (
        "The user lacks the proper permissions to account the given expense or invoice."
    )


register_exception(AccountingPermissionDeniedProblem)


class PaymentPermissionDeniedProblem(APIException):
    status_code = 403
    default_code = "payment_permission_denied"
    title = "Permission denied for payment expense/invoice"
    default_detail = (
        "The user lacks the proper permissions to pay this expense or invoice."
    )


register_exception(PaymentPermissionDeniedProblem)


class MultipleReceiversProblem(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_code = "multiple_receivers"
    title = "More than one receiver in payment"
    default_detail = "Only one user's expenses can be included in one payment."


register_exception(MultipleReceiversProblem)


class AlreadyReimbursedProblem(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "already_reimbursed"
    title = "Resource is already reimbursed"
    default_detail = "This expense or invoice is already reimbursed."


register_exception(AlreadyReimbursedProblem)


class NoExpensesProblem(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_code = "no_expenses"
    title = "No expenses in payment"
    default_detail = "A payment must include at least one expense."


register_exception(NoExpensesProblem)
