import json
from datetime import date, datetime, timedelta
from decimal import *
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.functions import Length
from django.db import connection
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponseBadRequest, JsonResponse, Http404
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_GET, require_POST

from cashflow import dauth
from cashflow import fortnox
from expenses.models import Expense, ExpensePart, BankAccount, Comment, Profile, FortnoxAuthToken, FortnoxAccounts
from invoices.models import Invoice, InvoicePart


@require_GET
@login_required
@user_passes_test(lambda u: u.profile.is_admin())
def index(request):
    """
    Displays the admin index page.
    """
    return render(request, 'admin/main.html')


@require_GET
@login_required
@user_passes_test(lambda u: u.profile.may_view_attestable())
def attest_overview(request):
    """
    Displays the attest overview list.
    """
    return render(request, 'admin/attest/overview.html', {
        'expenses': json.dumps(
            [expense.to_dict() for expense in Expense.view_attestable(request.user)],
            default=json_serial),
        'invoices': json.dumps(
            [invoice.to_dict() for invoice in Invoice.view_attestable(request.user)],
            default=json_serial)
    })


@require_POST
@login_required
@user_passes_test(lambda u: u.profile.may_attest_some())
def attest_expense_part(request, pk):
    try:
        expense_part = ExpensePart.objects.get(pk=int(pk))
    except ObjectDoesNotExist:
        raise Http404("Kvittodelen finns inte")

    if not request.user.profile.may_attest(expense_part):
        messages.error(request, 'Du får inte attestera denna kvittodel')
        return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk': expense_part.expense.id}))

    if request.user.username == expense_part.expense.owner.user.username:
        messages.error(request, 'Du kan inte attestera dina egna kvitton')
        return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk': expense_part.expense.id}))

    expense_part.attest(request.user)

    if expense_part.expense.is_attested():
        return HttpResponseRedirect(reverse('admin-attest'))
    return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk': expense_part.expense.id}))

@require_POST
@login_required
@user_passes_test(lambda u: u.profile.is_admin())
def unattest_expense(request, pk):
    try:
        expense = Expense.objects.get(pk=int(pk))
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")
    if expense.reimbursement:
        # This shouldn't be a 404 but i couldn't import Http400 and I don't care
        raise Http404("Utlägget har redan betalats ut")
    try:
        expense_parts = ExpensePart.objects.filter(expense_id=int(pk))

        if not request.user.profile.is_admin():
            return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk': int(pk)}))

        for part in expense_parts:
            part.unattest(request.user)
    except ObjectDoesNotExist:
        raise Http404("Kvittodelarna finns inte")

    return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk': int(pk)}))


@require_POST
@login_required
@user_passes_test(lambda u: u.profile.may_attest_some())
def attest_invoice_part(request, pk):
    try:
        invoice_part = InvoicePart.objects.get(pk=int(pk))
    except ObjectDoesNotExist:
        raise Http404("Fakturadelen finns inte")

    if not request.user.profile.may_attest(invoice_part):
        messages.error(request, 'Du får inte attestera denna fakturadel')
        return HttpResponseRedirect(reverse('invoices-show', kwargs={'pk': invoice_part.invoice.id}))

    invoice_part.attest(request.user)

    if invoice_part.invoice.is_attested():
        return HttpResponseRedirect(reverse('admin-attest'))
    return HttpResponseRedirect(reverse('invoices-show', kwargs={'pk': invoice_part.invoice.id}))


@require_GET
@login_required
@user_passes_test(lambda u: u.profile.may_view_confirmable())
def confirm_overview(request):
    """
    Shows a list of confirmable receipts and lets user confirm them.
    """
    return render(request, 'admin/confirm/overview.html', {
        'confirmable_expenses': json.dumps(
            [expense.to_dict() for expense in Expense.objects.filter(confirmed_by=None).exclude(is_flagged=True).order_by('id').distinct()],
            default=json_serial)
    })


@require_GET
@login_required
@user_passes_test(lambda u: u.profile.may_view_payable())
def pay_overview(request):
    """
    Shows a list of all payable expenses and lets user pay them.
    """
    return render(request, 'admin/pay/overview.html', {
        'invoices': json.dumps([invoice.to_dict() for invoice in Invoice.payable()], default=json_serial),
        'expenses': json.dumps([expense.to_dict() for expense in Expense.payable()], default=json_serial),
        'accounts': json.dumps([s.name for s in BankAccount.objects.all().order_by('name')])
    })


@require_POST
@login_required
@user_passes_test(lambda u: u.profile.may_pay())
def invoice_pay(request, pk):
    try:
        invoice = Invoice.objects.get(pk=pk)
    except ObjectDoesNotExist:
        raise Http404("Fakturan finns inte")

    if not invoice.is_payable():
        messages.error(request, 'Fakturan är inte attesterad än.')
        return HttpResponseRedirect(reverse('invoices-show', kwargs={'pk': invoice.id}))

    invoice.pay(request.user)
    return HttpResponseRedirect(reverse('admin-pay'))


@require_GET
@login_required
@user_passes_test(lambda u: u.profile.may_view_accountable())
def account_overview(request):
    return render(request, 'admin/account/overview.html', {
        'expenses': json.dumps(
            [expense.to_dict() for expense in Expense.view_accountable(request.user)],
            default=json_serial),
        'invoices': json.dumps(
            [invoice.to_dict() for invoice in Invoice.view_accountable(request.user)],
            default=json_serial)
    })

@require_GET
@login_required
@user_passes_test(lambda u: u.profile.may_view_account())
def fortnox_auth(request):
    return HttpResponseRedirect(fortnox.FortnoxAPI.get_auth_code())

@login_required
@user_passes_test(lambda u: u.profile.may_firmatecknare())
def fortnox_auth_complete(request):
    auth_code = fortnox.FortnoxAPI.get_value_from_callback_url(request.get_full_path())
    get_tokens = fortnox.FortnoxAPI.get_access_token(auth_code)
    access_token = get_tokens['access_token']
    refresh_token = get_tokens['refresh_token']
    expires_in = get_tokens['expires_in']
    token_parts = FortnoxAuthToken.objects.all().delete()
    token_parts = FortnoxAuthToken(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=datetime.now() + timedelta(0, expires_in)
    )   
    token_parts.save()

    return render(request, 'admin/auth/overview.html', {
        'access_token': json.dumps(access_token, indent=4),
        'refresh_token': refresh_token,
        'expires_in': expires_in
    })

@login_required
def fortnox_auth_refresh(request):
    token = FortnoxAuthToken.objects.all().first()
    new_token = fortnox.FortnoxAPI.get_access_token_from_refresh_token(token.refresh_token)
    token = FortnoxAuthToken.objects.all().delete()
    token = FortnoxAuthToken(
        access_token=new_token['access_token'],
        refresh_token=new_token['refresh_token'],
        expires_at=datetime.now() + timedelta(0, new_token['expires_in'])
    )
    token.save()


#@require_GET
@login_required
@user_passes_test(lambda u: u.profile.may_firmatecknare())
def fortnox_auth_test(request):
    token = FortnoxAuthToken.objects.all().first()
    if token is None:
        return HttpResponseBadRequest("No token found")
    company_info = fortnox.FortnoxAPI.get_company_info(token.access_token)
    # If company_info returns {'message': 'unauthorized'} then the token is invalid
    accounts = fortnox.FortnoxAPI.get_accounts(token.access_token, 13)
    accountchart = fortnox.FortnoxAPI.get_api_request(token.access_token, 'accountcharts')
    voucher_series = fortnox.FortnoxAPI.get_voucher_series(token.access_token)
    cost_centers = fortnox.FortnoxAPI.get_cost_centers(token.access_token)
    expenses = fortnox.FortnoxAPI.get_api_request(token.access_token, 'expenses')
    labels = fortnox.FortnoxAPI.get_api_request(token.access_token, 'labels')
    predefined_accounts = fortnox.FortnoxAPI.get_api_request(token.access_token, 'predefinedaccounts')
    return render(request, 'admin/auth/test.html', {
        'company_info': company_info,
        'accounts': accounts,
        'accountchart': accountchart,
        'voucher_series': voucher_series,
        'cost_centers': cost_centers,
        'expenses': expenses,
        'labels': labels,
        'predefined_accounts': predefined_accounts
    })

@login_required
@user_passes_test(lambda u: u.profile.may_firmatecknare())
def fortnox_import_accounts_to_db(request):
    token = FortnoxAuthToken.objects.all().first()
    if token is None:
        return HttpResponseBadRequest("No token found")
    # Get all accounts from Fortnox thru all pages and save them to the database
    page_number = 0
    
    FortnoxAccounts.objects.all().delete()
    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE expenses_fortnoxaccounts RESTART IDENTITY;")
    
    while True:
        accounts = fortnox.FortnoxAPI.get_accounts(token.access_token, page_number)
        if page_number > accounts.get('MetaInformation', {}).get('@TotalPages', 0):
            break
        for account in accounts['Accounts']:
            account_db = FortnoxAccounts(
                URL="None" if account.get('@url') is None else account.get('@url'),
                Active="None" if account.get('Active') is None else account.get('Active'),
                BalanceBroughtForward=0 if account.get('BalanceBroughtForward') is None else account.get('BalanceBroughtForward'),
                CostCenter="None" if account.get('CostCenter') is None else account.get('CostCenter'),
                CostCenterSettings="None" if account.get('CostCenterSettings') is None else account.get('CostCenterSettings'),
                Description="None" if account.get('Description') is None else account.get('Description'),
                Number=account.get('Number'),
                Project="None" if account.get('Project') is None else account.get('Project'),
                ProjectSettings="None" if account.get('ProjectSettings') is None else account.get('ProjectSettings'),
                SRU=0 if account.get('SRU') is None else account.get('SRU'),
                VATCode="None" if account.get('VATCode') is None else account.get('VATCode'),
                Year=0 if account.get('Year') is None else account.get('Year')
            )
            account_db.save()
        page_number += 1
    return HttpResponseRedirect(reverse('admin-auth-test'))

@require_GET
@login_required
@require_GET
@login_required
@user_passes_test(lambda u: u.profile.may_firmatecknare())
def fortnox_auth_search(request):
    token = FortnoxAuthToken.objects.first()
    if token is None:
        return JsonResponse({'error': 'No token found'})

    search_query = request.GET.get('search')
    
    search_results = FortnoxAccounts.objects.filter(
        Description__icontains=search_query
    ) | FortnoxAccounts.objects.filter(Number__icontains=search_query)

    results_list = list(search_results.values('Number', 'Description'))
    return JsonResponse({'accounts': results_list})


@require_http_methods(["GET", "POST"])
@login_required
@user_passes_test(lambda u: u.profile.may_account_some())
def edit_expense_verification(request, pk):
    try:
        expense = Expense.objects.get(pk=pk)
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")

    if not request.user.profile.may_account(expense=expense):
        return HttpResponseForbidden("Du har inte rättigheter att bokföra det här")
    if expense.reimbursement is None:
        return HttpResponseBadRequest("Du kan inte bokföra det här utlägget än")

    if request.method == 'POST':
        expense.verification = request.POST['verification']
        expense.save()

        Comment(
            author=request.user.profile,
            expense=expense,
            content="Ändrade verifikationsnumret till: " + expense.verification
        ).save()

        return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk': expense.id}))
    else:
        return render(request, 'expenses/edit-verification.html', {
            "expense": expense,
            "expense_parts": expense.expensepart_set.all()
        })


@require_POST
def confirm_expense(request, pk):
    try:
        expense = Expense.objects.get(pk=pk)

        if not request.user.profile.may_confirm():
            return HttpResponseForbidden("Du har inte rättigheterna för att bekräfta kvittons giltighet")

        expense.confirmed_by = request.user
        expense.confirmed_at = date.today()
        expense.save()

        comment = Comment(
            expense=expense,
            author=request.user.profile,
            content='Jag har bekräftat kvittots giltighet.'
        )
        comment.save()

        return HttpResponseRedirect(reverse('admin-confirm'))
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")


@require_POST
def unconfirm_expense(request, pk):
    try:
        expense = Expense.objects.get(pk=pk)

        if not request.user.profile.may_unconfirm():
            return HttpResponseForbidden("Du har inte rättigheterna för att ta bort bekräftelse av kvittons giltighet")

        expense.confirmed_by = None
        expense.confirmed_at = None
        expense.save()

        comment = Comment(
            expense=expense,
            author=request.user.profile,
            content='Jag tar bort bekräftelsen av kvittots giltighet.'
        )
        comment.save()

        return HttpResponseRedirect(reverse('admin-confirm'))
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")


@require_POST
@login_required
@user_passes_test(lambda u: u.profile.may_account_some())
def set_verification(request, expense_pk):
    try:
        expense = Expense.objects.get(pk=expense_pk)
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")

    if not request.user.profile.may_account(expense=expense):
        return HttpResponseForbidden("Du har inte rättigheter att bokföra det här")
    if expense.reimbursement is None:
        return HttpResponseBadRequest("Du kan inte bokföra det här utlägget än")

    expense.verification = request.POST['verification']
    expense.save()

    comment = Comment(
        author=request.user.profile,
        expense=expense,
        content="Bokförde med verifikationsnumret: " + expense.verification
    )
    comment.save()

    return HttpResponseRedirect(reverse('admin-account'))


@require_POST
@login_required
@user_passes_test(lambda u: u.profile.may_account_some())
def invoice_set_verification(request, invoice_pk):
    try:
        invoice = Invoice.objects.get(pk=invoice_pk)
    except ObjectDoesNotExist:
        raise Http404("Fakturan finns inte")

    if not request.user.profile.may_account(invoice=invoice):
        return HttpResponseForbidden("Du har inte rättigheter att bokföra det här")
    if invoice.payed_by is None:
        return HttpResponseBadRequest("Du kan inte bokföra den här fakturan än")

    invoice.verification = request.POST['verification']
    invoice.save()

    comment = Comment(
        author=request.user.profile,
        invoice=invoice,
        content="Bokförde med verifikationsnumret: " + invoice.verification
    )
    comment.save()

    return HttpResponseRedirect(reverse('admin-account'))


@require_GET
@login_required
@user_passes_test(lambda u: u.profile.is_admin())
def expense_overview(request):
    """
    Lists all expenses.
    """
    cost_centre = request.GET.get('cost_centre')
    expenses_list = Expense.objects.order_by('-id', '-expense_date').distinct()
    if cost_centre is not None and cost_centre != '':
        expenses_list = expenses_list.filter(expensepart__cost_centre=cost_centre)
    expenses_list = expenses_list.all()
    paginator = Paginator(expenses_list, 25)
    page = request.GET.get('page')

    try:
        expenses = paginator.page(page)
    except PageNotAnInteger:
        expenses = paginator.page(1)
    except EmptyPage:
        expenses = paginator.page(paginator.num_pages)
    
    pages = {
        'number': expenses.number,
        'previous_page_number': expenses.previous_page_number,
        'next_page_number': expenses.next_page_number,
        'page_range': expenses.paginator.page_range,
        'num_pages': expenses.paginator.num_pages,
        'has_next': expenses.has_next,
    }
    return render(request, 'admin/expenses/overview.html', {
        'expenses': json.dumps(
            [x.to_dict() for x in expenses], 
            default=json_serial),
        'pages': pages,
        'cost_centres': json.dumps(
            [x['cost_centre'] for x in ExpensePart.objects.values('cost_centre').distinct()]),
        'cost_centre': cost_centre if cost_centre is not None else ''
    })


@require_GET
@login_required
@user_passes_test(lambda u: u.profile.is_admin())
def user_overview(request):
    """
    Lists all users.
    """
    paginator = Paginator(Profile.objects.order_by('-id').all(), 25)
    page = request.GET.get('page')

    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    return render(request, 'admin/users/overview.html', {
        'users': users
    })


@require_GET
@login_required
@user_passes_test(lambda u: u.profile.is_admin())
def invoice_overview(request):
    """
    Lists all invoices.
    """
    cost_centre = request.GET.get('cost_centre')
    invoices_list = Invoice.objects.order_by('-id').distinct()
    if cost_centre is not None and cost_centre != '':
        invoices_list = invoices_list.filter(invoicepart__cost_centre=cost_centre)
    invoices_list = invoices_list.all()
    paginator = Paginator(invoices_list, 25)
    page = request.GET.get('page')

    try:
        invoices = paginator.page(page)
    except PageNotAnInteger:
        invoices = paginator.page(1)
    except EmptyPage:
        invoices = paginator.page(paginator.num_pages)

    return render(request, 'admin/invoices/overview.html', {
        'invoices': invoices,
        'cost_centres': json.dumps(
            [x['cost_centre'] for x in ExpensePart.objects.values('cost_centre').distinct()]),
        'cost_centre': cost_centre if cost_centre is not None else ''
    })


@require_GET
@login_required
@user_passes_test(lambda u: u.profile.is_admin())
def search_verification(request):
    return render(request, 'admin/search-verification.html')


@require_POST
@login_required
@user_passes_test(lambda u: u.profile.is_admin())
def search_verification_response(request):
    if len(request.POST['query']) < 1:
        return JsonResponse({'invoices': [], 'expenses': []})

    invoices = Invoice.objects.filter(verification__contains=request.POST['query']).all()
    expenses = Expense.objects.filter(verification__contains=request.POST['query']).all()
    return JsonResponse({
        'invoices': [invoice.to_dict() for invoice in invoices[:10]],
        'expenses': [expense.to_dict() for expense in expenses[:10]]
    })


@require_GET
@login_required
@user_passes_test(lambda u: u.profile.is_admin())
def list_verification(request):
    years = range(2017, datetime.now().year + 1)
    year = request.GET.get('year')

    year = year if year is not None and year != '' else datetime.now().year

    verification_list = Expense.objects \
        .filter(expense_date__year=year, verification__regex=r'E') \
        .order_by(Length('verification').asc(), 'verification') \
        .all()

    paginator = Paginator(verification_list, 25)
    page = request.GET.get('page')

    try:
        verifications = paginator.page(page)
    except PageNotAnInteger:
        verifications = paginator.page(1)
    except EmptyPage:
        verifications = paginator.page(paginator.num_pages)

    return render(request, 'admin/list-verification.html', {
        'expenses': verifications,
        'years': years,
        'year': year,
    })


class FakeFloat(float):
    # noinspection PyMissingConstructor
    def __init__(self, value):
        self._value = value

    def __repr__(self):
        return str(self._value)


def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return FakeFloat(obj)
    raise TypeError("Type %s not serializable" % type(obj))
