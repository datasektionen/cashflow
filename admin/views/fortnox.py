import secrets
from datetime import timedelta

import structlog
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

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
from fortnox.api_client import AuthCodeGrant
from fortnox.django import FortnoxRequest, require_fortnox_permission
from fortnox.models import ServiceAccount
from invoices.models import Invoice

logger = structlog.get_logger(__name__)


class CSRFValidationError(PermissionError):
    pass


@require_GET
@login_required
@require_fortnox_permission
def get_auth_code(request):
    """Retrieves an auth code from Fortnox.

    When this view is triggered, the user will be redirected to a Fortnox
    login page. Upon successful authentication, the user will be redirected
    to a success page.
    """

    # Generate a token for CSRF protection
    csrf_token = secrets.token_urlsafe(32)
    request.session["fortnox_csrf_token"] = csrf_token

    logger.info("started authentication flow for Fortnox service account")

    redirect_uri = request.build_absolute_uri(reverse("fortnox-auth-complete"))
    return HttpResponseRedirect(
        request.fortnox.build_auth_code_url(redirect_uri, csrf_token)
    )


@login_required
@require_fortnox_permission
def auth_complete(request):
    redirect_uri = request.build_absolute_uri(reverse("fortnox-auth-complete"))

    # Validate CSRF token integrity
    client_token = request.session.get("fortnox_csrf_token")
    response_token = request.GET.get("state")
    match client_token, response_token:
        case _, None:
            raise CSRFValidationError("CSRF token missing from API response")
        case None, _:
            raise CSRFValidationError("CSRF token missing from session storage")
        case a, b if a != b:
            raise CSRFValidationError("Mismatched CSRF tokens")
        case a, b if a == b:
            # OK
            request.session.delete("fortnox_csrf_token")

    # Get auth code from URL parameters
    match request.GET.get("code"), request.GET.get("error"):
        case None, e:
            # logger.error(f"Error when authenticating {request.user} to Fortnox: {e}")
            logger.error(
                f"fortnox error when authenticating",
                error_message=e,
            )
            return redirect(reverse("admin-index"))
        case auth_code, _:
            response = request.fortnox.retrieve_access_token(
                AuthCodeGrant(code=auth_code, redirect_uri=redirect_uri)
            )
            ServiceAccount.objects.all().delete()
            new = ServiceAccount.objects.create(
                authenticated_by=request.user,
                access_token=response.access_token,
                refresh_token=response.refresh_token,
                expires_at=timezone.now() + timedelta(seconds=response.expires_in),
            )
            logger.info(
                "fortnox successfully authenticated",
                token_id=new.pk,
                token_expires_at=new.expires_at,
            )

    return redirect(reverse("fortnox-overview"))


@login_required
@require_fortnox_permission
def disconnect(request):
    """Disconnects (logs out) the user from Fortnox. Deletes saved tokens and then redirects to main admin page."""
    try:
        token = ServiceAccount.objects.get()
        token_id = token.pk or None
        ServiceAccount.objects.get().delete()
        logger.warning("fortnox service manually disconnected", token_id=token_id)
    except ServiceAccount.DoesNotExist:
        pass

    return redirect(reverse("admin-index"))


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


@login_required
def overview(request: FortnoxRequest):
    service_account = ServiceAccount.objects.first()
    is_connected = (
        service_account is not None and service_account.expires_at > timezone.now()
    )
    return render(
        request,
        "admin/fortnox/overview.html",
        {
            "service_account": service_account,
            "is_connected": is_connected,
        },
    )
