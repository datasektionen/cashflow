import json
from datetime import date, datetime
from decimal import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.functions import Length
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponseBadRequest, JsonResponse, Http404
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_GET, require_POST

from cashflow import dauth
from expenses.models import Expense, ExpensePart, BankAccount, Comment, Profile
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
@user_passes_test(lambda u: u.profile.may_attest())
def attest_overview(request):
    """
    Displays the attest overview list.
    """
    return render(request, 'admin/attest/overview.html', {
        'expenses': json.dumps(
            [expense.to_dict() for expense in Expense.attestable(request.user.profile.may_attest(), request.user)],
            default=json_serial),
        'invoices': json.dumps(
            [invoice.to_dict() for invoice in Invoice.attestable(request.user.profile.may_attest(), request.user)],
            default=json_serial)
    })


@require_POST
@login_required
@user_passes_test(lambda u: u.profile.may_attest())
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
@user_passes_test(lambda u: u.profile.may_attest())
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
@user_passes_test(lambda u: u.profile.may_confirm())
def confirm_overview(request):
    """
    Shows a list of confirmable receipts and lets user confirm them.
    """
    return render(request, 'admin/confirm/overview.html', {
        'confirmable_expenses': json.dumps(
            [expense.to_dict() for expense in Expense.objects.filter(confirmed_by=None).order_by('id').distinct()],
            default=json_serial)
    })


@require_GET
@login_required
@user_passes_test(lambda u: u.profile.may_pay())
def pay_overview(request):
    """
    Shows a list of all payable expenses and lets user pay them.
    """
    return render(request, 'admin/pay/overview.html', {
        'expenses': json.dumps([expense.to_dict() for expense in Expense.payable()], default=json_serial),
        'invoices': json.dumps([invoice.to_dict() for invoice in Invoice.payable()], default=json_serial),
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
@user_passes_test(lambda u: u.profile.may_account())
def account_overview(request):
    return render(request, 'admin/account/overview.html', {
        'expenses': json.dumps(
            [expense.to_dict() for expense in Expense.accountable(request.user.profile.may_account())],
            default=json_serial),
        'invoices': json.dumps(
            [invoice.to_dict() for invoice in Invoice.accountable(request.user.profile.may_account())],
            default=json_serial)
    })


@require_http_methods(["GET", "POST"])
@login_required
@user_passes_test(lambda u: u.profile.may_account())
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


def confirm_expense(request, pk):
    if request.method == 'POST':
        try:
            expense = Expense.objects.get(pk=pk)

            if not dauth.has_permission('confirm', request):
                return HttpResponseForbidden("Du har inte rättigheterna för att se den här sidan")

            expense.confirmed_by = request.user
            expense.confirmed_at = date.today()
            expense.save()

            comment = Comment(
                expense=expense,
                author=request.user.profile,
                content='Jag bekräftar att kvittot finns i pärmen.'
            )
            comment.save()

            return HttpResponseRedirect(reverse('expenses-action-confirm'))
        except ObjectDoesNotExist:
            raise Http404("Utlägget finns inte")
    else:
        raise Http404()


@require_POST
@login_required
@user_passes_test(lambda u: u.profile.may_account())
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

    return HttpResponseRedirect(reverse('admin-action-account'))


@require_POST
@login_required
@user_passes_test(lambda u: u.profile.may_account())
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

    return HttpResponseRedirect(reverse('admin-action-account'))


@require_GET
@login_required
@user_passes_test(lambda u: u.profile.is_admin())
def expense_overview(request):
    """
    Lists all expenses.
    """
    committee = request.GET.get('committee')
    expenses_list = Expense.objects.order_by('verification', '-id')
    if committee is not None and committee != '':
        expenses_list = expenses_list.filter(expensepart__committee_name=committee)
    expenses_list = expenses_list.all()
    paginator = Paginator(expenses_list, 25)
    page = request.GET.get('page')

    try:
        expenses = paginator.page(page)
    except PageNotAnInteger:
        expenses = paginator.page(1)
    except EmptyPage:
        expenses = paginator.page(paginator.num_pages)

    return render(request, 'admin/expenses/overview.html', {
        'expenses': expenses,
        'committees': json.dumps(
            [x['committee_name'] for x in ExpensePart.objects.values('committee_name').distinct()]),
        'committee': committee if committee is not None else ''
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
    committee = request.GET.get('committee')
    invoices_list = Invoice.objects.order_by('verification', '-id')
    if committee is not None and committee != '':
        invoices_list = invoices_list.filter(invoicepart__committee_name=committee)
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
        'committees': json.dumps(
            [x['committee_name'] for x in ExpensePart.objects.values('committee_name').distinct()]),
        'committee': committee if committee is not None else ''
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
    return render(request, 'admin/list-verification.html', {
        'expenses': json.dumps([expense.to_dict() for expense in Expense.objects.filter(verification__regex=r'E')
                               .order_by(Length('verification').asc(), 'verification').all()], default=json_serial),
        'years': range(2017, datetime.now().year + 1)
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
