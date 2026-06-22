import secrets
from datetime import timedelta

import structlog
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from cashflow.exceptions import AccountingPermissionDeniedError
from expenses.models import Expense, Comment
from fortnox import FortnoxNotFound
from fortnox.api_client import AuthCodeGrant
from fortnox.api_client.models import VoucherRow, VoucherCreate
from fortnox.django import FortnoxRequest, require_fortnox_permission
from fortnox.exceptions import (
    FortnoxRecordMissingError,
    CashflowVerificationMissingError,
    AlreadyAccountedError,
)
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


@require_POST
def account_expense(request: FortnoxRequest, **kwargs):
    with transaction.atomic():
        expense = Expense.objects.select_for_update().get(id=kwargs["id"])

        if not request.user.profile.may_account(expense):
            error = AccountingPermissionDeniedError(
                detail=f"{request.user} lacks permission to account the expense {expense}. Most likely this means that no cost centres are within the user's scope(s)."
            )
            return JsonResponse(error.to_dict(), status=403)

        # This is used to uniquely identify the cashflow expense in Fortnox
        description = settings.FORTNOX_DESCRIPTION_FORMAT.format(
            description=expense.description, kind="expense", id=expense.id
        )

        if expense.verification:
            # Race condition or sync issue between Cashflow and Fortnox
            try:
                request.fortnox_service.retrieve_voucher(
                    settings.FORTNOX_EXPENSE_VOUCHER_SERIES,
                    int(expense.verification[1:]),
                )
                error_dict = AlreadyAccountedError(
                    detail=f"Expense [{expense.id}]: '{expense.description}' is already accounted in Fortnox as {expense.verification}"
                ).to_dict()
                return JsonResponse(error_dict, status=409)
            except FortnoxNotFound:
                # Possible mismatch between our records and Fortnox
                # This should probably be extended with some type of warning system for administrators
                logger.error(
                    "fortnox voucher record missing",
                    expense_id=expense.id,
                    expense_voucher_number=expense.verification,
                    user_id=request.user.id,
                )
                error_dict = FortnoxRecordMissingError(
                    detail=f"The expense [{expense.id}]: '{expense.description}' is registered in Cashflow as {expense.verification}, but no matching record was found on Fortnox."
                ).to_dict()
                return JsonResponse(error_dict, status=409)

        # Sanity check in the rare case that a record exists on Fortnox but not in Cashflow
        try:
            voucher = request.fortnox_service.find_voucher(Description=description)
            logger.error(
                "expense missing verification in Cashflow",
                expense_id=expense.id,
                fortnox_voucher_series=voucher.VoucherSeries,
                fortnox_voucher_number=voucher.VoucherNumber,
                fortnox_voucher_comments=voucher.Comments,
            )

            error_dict = CashflowVerificationMissingError(
                detail=f"The expense [{expense.id}]: '{expense.description}' was found on Fortnox but it has no registered verification in Cashflow"
            ).to_dict()
            return JsonResponse(error_dict, status=409)

        except FortnoxNotFound:
            pass

        voucher_rows: list[VoucherRow] = []
        credit_row = VoucherRow(
            Account=settings.FORTNOX_EXPENSE_CREDIT_ACCOUNT,
            Credit=float(expense.total_amount()),
        )
        voucher_rows.append(credit_row)

        for part in expense.parts.all():
            acct = int(request.POST[f"part-{part.id}-account"])
            cc = request.POST[f"part-{part.id}-cost-center"]
            debit_row = VoucherRow(
                Account=acct, CostCenter=cc, Debit=float(part.amount)
            )
            voucher_rows.append(debit_row)

        created = request.fortnox_service.create_voucher(
            VoucherCreate(
                Description=description,
                TransactionDate=expense.expense_date.strftime("%Y-%m-%d"),
                VoucherRows=voucher_rows,
                VoucherSeries=settings.FORTNOX_EXPENSE_VOUCHER_SERIES,
            )
        )
        expense.verification = (
            f"{settings.FORTNOX_EXPENSE_VOUCHER_SERIES}{created.VoucherNumber}"
        )
        expense.save()

    comment = Comment(
        author=request.user.profile,
        expense=expense,
        content="Bokförde med verifikationsnumret: " + expense.verification,
    )
    comment.save()

    return redirect("admin-account")


@require_POST
def account_invoice(request: FortnoxRequest, **kwargs):
    with transaction.atomic():
        invoice = Invoice.objects.select_for_update().get(id=kwargs["id"])

        if not request.user.profile.may_account(invoice=invoice):
            error = AccountingPermissionDeniedError(
                detail=f"{request.user} lacks permission to account the invoice {invoice}. Most likely this means that no cost centres are within the user's scope(s)."
            )
            return JsonResponse(error.to_dict(), status=403)

        # This is used to uniquely identify the cashflow invoice in Fortnox
        description = settings.FORTNOX_DESCRIPTION_FORMAT.format(
            description=invoice.description, kind="invoice", id=invoice.id
        )

        if invoice.verification:
            # Race condition or sync issue between Cashflow and Fortnox
            try:
                request.fortnox_service.retrieve_voucher(
                    settings.FORTNOX_INVOICE_VOUCHER_SERIES,
                    int(invoice.verification[1:]),
                )
                error_dict = AlreadyAccountedError(
                    detail=f"Invoice [{invoice.id}]: '{invoice.description}' is already accounted in Fortnox as {invoice.verification}"
                ).to_dict()
                return JsonResponse(error_dict, status=409)
            except FortnoxNotFound:
                # Possible mismatch between our records and Fortnox
                # This should probably be extended with some type of warning system for administrators
                logger.error(
                    "fortnox voucher record missing",
                    invoice_id=invoice.id,
                    invoice_voucher_number=invoice.verification,
                    user_id=request.user.id,
                )
                error_dict = FortnoxRecordMissingError(
                    detail=f"The invoice [{invoice.id}]: '{invoice.description}' is registered in Cashflow as {invoice.verification}, but no matching record was found on Fortnox."
                ).to_dict()
                return JsonResponse(error_dict, status=409)

        # Sanity check in the rare case that a record exists on Fortnox but not in Cashflow
        try:
            voucher = request.fortnox_service.find_voucher(Description=description)
            logger.error(
                "invoice missing verification in Cashflow",
                invoice_id=invoice.id,
                fortnox_voucher_series=voucher.VoucherSeries,
                fortnox_voucher_number=voucher.VoucherNumber,
                fortnox_voucher_comments=voucher.Comments,
            )

            error_dict = CashflowVerificationMissingError(
                detail=f"The invoice [{invoice.id}]: '{invoice.description}' was found on Fortnox but it has no registered verification in Cashflow"
            ).to_dict()
            return JsonResponse(error_dict, status=409)

        except FortnoxNotFound:
            pass

        voucher_rows: list[VoucherRow] = []
        credit_row = VoucherRow(
            Account=settings.FORTNOX_INVOICE_CREDIT_ACCOUNT,
            Credit=float(invoice.total_amount()),
        )
        voucher_rows.append(credit_row)

        for part in invoice.parts.all():
            acct = int(request.POST[f"part-{part.id}-account"])
            cc = request.POST[f"part-{part.id}-cost-center"]
            debit_row = VoucherRow(
                Account=acct, CostCenter=cc, Debit=float(part.amount)
            )
            voucher_rows.append(debit_row)

        created = request.fortnox_service.create_voucher(
            VoucherCreate(
                Description=description,
                TransactionDate=invoice.invoice_date.strftime("%Y-%m-%d"),
                VoucherRows=voucher_rows,
                VoucherSeries=settings.FORTNOX_INVOICE_VOUCHER_SERIES,
            )
        )
        invoice.verification = (
            f"{settings.FORTNOX_INVOICE_VOUCHER_SERIES}{created.VoucherNumber}"
        )
        invoice.save()

    comment = Comment(
        author=request.user.profile,
        invoice=invoice,
        content="Bokförde med verifikationsnumret: " + invoice.verification,
    )
    comment.save()

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
