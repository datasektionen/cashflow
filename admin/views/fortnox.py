import structlog
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.exceptions import (
    UnauthorizedAccountingError,
    AlreadyAccountedError,
    FortnoxRecordMissingError,
    CashflowVerificationMissingError,
)
from expenses.models import Expense
from fortnox.api.problems import (
    AlreadyAccountedProblem,
    CashflowVerificationMissingProblem,
    FortnoxRecordMissingProblem,
)
from fortnox.django import FortnoxRequest
from invoices.models import Invoice

logger = structlog.get_logger(__name__)


def _problem_response(exc) -> JsonResponse:
    return JsonResponse(
        {
            "type": f"/problems/{exc.default_code}",
            "title": exc.title,
            "detail": exc.detail,
            "status_code": exc.status_code,
        },
        status=exc.status_code,
    )


@require_POST
def account_expense(request: FortnoxRequest, **kwargs):
    with transaction.atomic():
        expense = Expense.objects.select_for_update().get(id=kwargs["id"])
        part_accounts = {
            part.id: (
                int(request.POST[f"part-{part.id}-account"]),
                request.POST[f"part-{part.id}-cost-center"],
            )
            for part in expense.parts.all()
        }
        try:
            expense.account(request.user, request.fortnox_service, part_accounts)  # type: ignore[arg-type]
        except UnauthorizedAccountingError:
            return JsonResponse({"detail": "Permission denied"}, status=403)
        except AlreadyAccountedError:
            return _problem_response(AlreadyAccountedProblem())
        except FortnoxRecordMissingError:
            return _problem_response(FortnoxRecordMissingProblem())
        except CashflowVerificationMissingError:
            return _problem_response(CashflowVerificationMissingProblem())

    return redirect("admin-account")


@require_POST
def account_invoice(request: FortnoxRequest, **kwargs):
    with transaction.atomic():
        invoice = Invoice.objects.select_for_update().get(id=kwargs["id"])
        part_accounts = {
            part.id: int(request.POST[f"part-{part.id}-account"])
            for part in invoice.parts.all()
        }
        try:
            invoice.account(request.user, request.fortnox_service, part_accounts)  # type: ignore[arg-type]
        except UnauthorizedAccountingError:
            return JsonResponse({"detail": "Permission denied"}, status=403)
        except AlreadyAccountedError:
            return _problem_response(AlreadyAccountedProblem())
        except FortnoxRecordMissingError:
            return _problem_response(FortnoxRecordMissingProblem())
        except CashflowVerificationMissingError:
            return _problem_response(CashflowVerificationMissingProblem())

    return redirect(reverse("admin-account"))
