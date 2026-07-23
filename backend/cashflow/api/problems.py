from drf_problems.utils import register
from rest_framework import exceptions


@register
class AccountingPermissionDeniedProblem(exceptions.PermissionDenied):
    status_code = 403
    default_code = "accounting_permission_denied"
    title = "Permission denied for accounting expense/invoice"
    default_detail = (
        "The user lacks the proper permissions to account the given expense or invoice."
    )
