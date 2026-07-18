from drf_problems.utils import register
from rest_framework import exceptions, status

from fortnox.api_client.exceptions import FortnoxDomainError


class ErrorToDictMixin:
    # (!) The following methods are meant as a "compatability" layer to allow these exceptions to work with
    # normal Django views, before we switch over to DRF only
    def __init__(self, detail: str | None = None):
        self.detail = detail or self.default_detail
        super().__init__(self.detail)

    def to_dict(self) -> dict:
        return {
            "type": f"/problems/{self.default_code}",
            "title": self.title,
            "detail": self.detail,
            "status_code": self.status_code,
        }


@register
class FortnoxRecordMissingError(
    exceptions.APIException, FortnoxDomainError, ErrorToDictMixin
):
    status_code = status.HTTP_409_CONFLICT
    default_code = "fortnox_record_missing"
    title = "Voucher record missing in Fortnox"
    default_detail = "Voucher record is missing in Fortnox"
    description = "A voucher that should exist on Fortnox was not found."


@register
class CashflowVerificationMissingError(
    exceptions.APIException, FortnoxDomainError, ErrorToDictMixin
):
    status_code = status.HTTP_409_CONFLICT
    default_code = "cashflow_verification_missing"
    title = "Verification missing in Cashflow"
    default_detail = "A voucher exists in Fortnox but the matching Cashflow expense has no verification recorded"
    description = "A voucher matching a Cashflow expense was found in Fortnox, but the expense has no verification recorded locally."


@register
class AlreadyAccountedError(
    exceptions.APIException, FortnoxDomainError, ErrorToDictMixin
):
    status_code = status.HTTP_409_CONFLICT
    default_code = "already_accounted"
    title = "Record is already accounted in Fortnox"
    default_detail = "This record has already been successfully accounted in Fortnox"
    description = "An attempt was made to account a record that has already been successfully accounted in Fortnox."


@register
class FortnoxServiceNotAvailableError(exceptions.APIException, ErrorToDictMixin):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "fortnox_service_not_available"
    title = "Fortnox service not available"
    default_detail = "The Fortnox integration service is not available."
