import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from expenses.models import Expense
from fortnox import FortnoxNotFound
from fortnox.api_client import AuthCodeGrant
from fortnox.api_client.models import VoucherRow, VoucherCreate
from fortnox.django import FortnoxRequest, require_fortnox_auth, require_fortnox_permission
from fortnox.models import APIUser
from invoices.models import Invoice

logger = logging.getLogger(__name__)


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
    request.session['fortnox_csrf_token'] = csrf_token

    redirect_uri = request.build_absolute_uri(reverse('fortnox-auth-complete'))
    return HttpResponseRedirect(request.fortnox.build_auth_code_url(redirect_uri, csrf_token))


@login_required
@require_fortnox_permission
def auth_complete(request):
    redirect_uri = request.build_absolute_uri(reverse('fortnox-auth-complete'))

    # Validate CSRF token integrity
    client_token = request.session.get('fortnox_csrf_token')
    response_token = request.GET.get('state')
    match client_token, response_token:
        case _, None:
            raise CSRFValidationError('CSRF token missing from API response')
        case None, _:
            raise CSRFValidationError('CSRF token missing from session storage')
        case a, b if a != b:
            raise CSRFValidationError('Mismatched CSRF tokens')
        case a, b if a == b:
            # OK
            request.session.delete('fortnox_csrf_token')

    # Get auth code from URL parameters
    match request.GET.get('code'), request.GET.get('error'):
        case None, e:
            logger.error(f"Error when authenticating {request.user} to Fortnox: {e}")
            return redirect(reverse('admin-index'))
        case auth_code, _:
            response = request.fortnox.retrieve_access_token(AuthCodeGrant(code=auth_code, redirect_uri=redirect_uri))
            APIUser.objects.all().delete()
            APIUser.objects.create(authenticated_by=request.user, access_token=response.access_token,
                refresh_token=response.refresh_token,
                expires_at=timezone.now() + timedelta(seconds=response.expires_in), )
            logger.info(f"{request.user} authenticated Fortnox service account")

    return redirect(reverse('fortnox-overview'))


@login_required
@require_fortnox_permission
def disconnect(request):
    """Disconnects (logs out) the user from Fortnox. Deletes saved tokens and then redirects to main admin page."""
    try:
        APIUser.objects.get().delete()
        logger.info(f"{request.user} disconnected Fortnox service account")
    except APIUser.DoesNotExist:
        logger.warning(f"{request.user} tried to disconnect Fortnox, but no service account was connected")

    return redirect(reverse('admin-index'))


@require_POST
def account_expense(request: FortnoxRequest, **kwargs):
    expense = Expense.objects.get(id=kwargs['id'])

    # This is used to uniquely identify the cashflow expense in Fortnox
    comment = f"{settings.FORTNOX_CASHFLOW_COMMENT_FORMAT.format(kind='expense', id=expense.id)} {expense.description}"

    # Sanity check in the rare case that the expense has already been accounted in Fortnox
    try:
        request.fortnox_service.find_voucher(Comments=comment)
        logger.warning(f"Expense {expense.id} is already accounted in Fortnox; aborting")
        return HttpResponse(f"Expense {expense.id} is already accounted in Fortnox", status=409,
                            content_type="text/plain")
    except FortnoxNotFound:
        pass

    voucher_rows: list[VoucherRow] = []
    credit_row = VoucherRow(Account=settings.FORTNOX_EXPENSE_CREDIT_ACCOUNT, Credit=float(expense.total_amount()))
    voucher_rows.append(credit_row)
    for part in expense.parts.all():
        acct = int(request.POST[f"part-{part.id}-account"])
        cc = request.fortnox_service.find_cost_center(Description=part.cost_centre)
        debit_row = VoucherRow(Account=acct, CostCenter=cc.Code, Debit=float(part.amount))
        voucher_rows.append(debit_row)

    created = request.fortnox_service.create_voucher(
        VoucherCreate(Description=expense.description, TransactionDate=expense.expense_date.strftime('%Y-%m-%d'),
                      VoucherRows=voucher_rows, VoucherSeries=settings.FORTNOX_EXPENSE_VOUCHER_SERIES,
                      Comments=comment))
    expense.verification = f"{settings.FORTNOX_EXPENSE_VOUCHER_SERIES}{created.VoucherNumber}"
    expense.save()
    logger.info(f"{request.user} accounted for expense {expense.id}")
    return redirect('admin-account')


@require_POST
def account_invoice(request: FortnoxRequest, **kwargs):
    invoice = Invoice.objects.get(id=kwargs['id'])

    # This is used to uniquely identify the cashflow invoice in Fortnox
    comment = f"{settings.FORTNOX_CASHFLOW_COMMENT_FORMAT.format(kind='invoice', id=invoice.id)} {invoice.description}"

    # Sanity check in the rare case that the invoice has already been accounted in Fortnox
    try:
        request.fortnox_service.find_voucher(Comments=comment)
        logger.warning(f"Invoice {invoice.id} is already accounted in Fortnox; aborting")
        return HttpResponse(f"Invoice {invoice.id} is already accounted in Fortnox", status=409,
                            content_type="text/plain")
    except FortnoxNotFound:
        pass

    voucher_rows: list[VoucherRow] = []
    credit_row = VoucherRow(Account=settings.FORTNOX_INVOICE_CREDIT_ACCOUNT, Credit=float(invoice.total_amount()))
    voucher_rows.append(credit_row)
    for part in invoice.parts.all():
        acct = int(request.POST[f"part-{part.id}-account"])
        cc = request.fortnox_service.find_cost_center(Description=part.cost_centre)
        debit_row = VoucherRow(Account=acct, CostCenter=cc.Code, Debit=float(part.amount))
        voucher_rows.append(debit_row)

    created = request.fortnox_service.create_voucher(
        VoucherCreate(Description=invoice.description, TransactionDate=invoice.invoice_date.strftime('%Y-%m-%d'),
                      VoucherRows=voucher_rows, VoucherSeries=settings.FORTNOX_INVOICE_VOUCHER_SERIES,
                      Comments=comment))
    invoice.verification = f"{settings.FORTNOX_INVOICE_VOUCHER_SERIES}{created.VoucherNumber}"
    invoice.save()
    logger.info(f"{request.user} accounted for invoice {kwargs['id']}")
    return redirect(reverse('admin-account'))


@login_required
@user_passes_test(lambda u: u.profile.may_firmatecknare())
@require_fortnox_auth
def overview(request: FortnoxRequest):
    accounts = request.fortnox_service.list_accounts()

    accounts = [account for account in accounts if account.Active]
    accounts = [a.model_dump() for a in accounts]

    return render(request, 'admin/fortnox/overview.html',
                  {'fortnox_user_name': request.user.get_full_name() or request.user.username, 'accounts': accounts, })
