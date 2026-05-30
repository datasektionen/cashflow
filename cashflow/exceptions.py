from drf_problems.utils import register
from rest_framework import exceptions

from core.exceptions import ErrorToDictMixin


@register
class AccountingPermissionDeniedError(exceptions.PermissionDenied, ErrorToDictMixin):
    status_code = 403
    default_code = "accounting_permission_denied"
    title = "Permission denied for accounting expense/invoice"
    default_detail = (
        "The user lacks the proper permissions to account the given expense or invoice."
    )
