from drf_problems.utils import register
from rest_framework import exceptions


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
class AccountingPermissionDeniedError(exceptions.PermissionDenied, ErrorToDictMixin):
    status_code = 403
    default_code = "accounting_permission_denied"
    title = "Permission denied for accounting expense/invoice"
    default_detail = (
        "The user lacks the proper permissions to account the given expense or invoice."
    )
