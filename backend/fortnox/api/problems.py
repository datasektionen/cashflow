from drf_problems.utils import register_exception
from rest_framework import exceptions, status

from fortnox.api_client.exceptions import FortnoxDomainError


class FortnoxRecordMissingProblem(exceptions.APIException, FortnoxDomainError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "fortnox_record_missing"
    title = "Voucher record missing in Fortnox"
    default_detail = "Voucher record is missing in Fortnox"
    description = "A voucher that should exist on Fortnox was not found."

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


register_exception(FortnoxRecordMissingProblem)


class CashflowVerificationMissingProblem(exceptions.APIException, FortnoxDomainError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "cashflow_verification_missing"
    title = "Verification missing in Cashflow"
    default_detail = "A voucher exists in Fortnox but the matching Cashflow record has no verification recorded"
    description = "A voucher matching a Cashflow record was found in Fortnox, but the record has no verification recorded locally."

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


register_exception(CashflowVerificationMissingProblem)


class AlreadyAccountedProblem(exceptions.APIException, FortnoxDomainError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "already_accounted"
    title = "Record is already accounted in Fortnox"
    default_detail = "This record has already been successfully accounted in Fortnox"
    description = "An attempt was made to account a record that has already been successfully accounted in Fortnox."

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


register_exception(AlreadyAccountedProblem)


class FortnoxServiceNotAvailableProblem(exceptions.APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "fortnox_service_not_available"
    title = "Fortnox service not available"
    default_detail = "The Fortnox integration service is not available."

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


register_exception(FortnoxServiceNotAvailableProblem)
