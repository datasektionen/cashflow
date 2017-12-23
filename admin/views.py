from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render
from django.core import serializers
from django.forms.models import model_to_dict
from datetime import date, datetime
from django.urls import reverse
from decimal import *
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from cashflow import dauth
from expenses.models import *
from invoices.models import *

"""
Displays the admin index page.
"""
@require_GET
@login_required
@user_passes_test(lambda u: u.profile.is_admin())
def index(request):
    return render(request, 'admin/main.html')

"""
Displays the attest overview list.
"""
@require_GET
@login_required
@user_passes_test(lambda u: u.profile.may_attest())
def attest_overview(request):
    return render(request, 'admin/attest/overview.html', {
        'attestable_expenses': json.dumps([expense.to_dict() for expense in Expense.attestable(request.user.profile.may_attest(), request.user)], default=json_serial)
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

"""
Shows a list of confirmable receipts and lets user confirm them.
"""
@require_GET
@login_required
@user_passes_test(lambda u: u.profile.may_confirm())
def confirm_overview(request):
    return render(request, 'admin/confirm/overview.html', {
        'confirmable_expenses': json.dumps([expense.to_dict() for expense in Expense.objects.filter(confirmed_by=None).order_by('id').distinct()], default=json_serial)
    })

"""
Shows a list of all payable expenses and lets user pay them.
"""
@require_GET
@login_required
@user_passes_test(lambda u: u.profile.may_pay())
def pay_overview(request):
    return render(request, 'admin/pay/overview.html', {
        'payable_expenses': json.dumps([expense.to_dict() for expense in Expense.payable()], default=json_serial),
        'accounts': json.dumps([s.name for s in BankAccount.objects.all().order_by('name')])
    })

@require_GET
@login_required
@user_passes_test(lambda u: u.profile.may_account())
def account_overview(request):
    return render(request, 'admin/account/overview.html', {
        'account_ready_expenses': json.dumps([expense.to_dict() for expense in Expense.accountable(request.user.profile.may_account())], default=json_serial)
    })

@require_http_methods(["GET", "POST"])
@login_required
@user_passes_test(lambda u: u.profile.may_account())
def edit_expense_verification(request, pk):
    try: expense = Expense.objects.get(pk=pk)
    except ObjectDoesNotExist: raise Http404("Utlägget finns inte")

    if not request.user.profile.may_account(expense=expense): return HttpResponseForbidden("Du har inte rättigheter att bokföra det här")
    if expense.reimbursement is None: return HttpResponseBadRequest("Du kan inte bokföra det här utlägget än")

    if request.method == 'POST':
        expense.verification = request.POST['verification']
        expense.save()

        Comment(
            author=request.user.profile,
            expense=expense,
            content="Ändrade verifikationsnumret till: " + expense.verification
        ).save()

        return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk':expense.id}))
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
    try: expense = Expense.objects.get(pk=expense_pk)
    except ObjectDoesNotExist: raise Http404("Utlägget finns inte")

    if not request.user.profile.may_account(expense=expense): return HttpResponseForbidden("Du har inte rättigheter att bokföra det här")
    if expense.reimbursement is None: return HttpResponseBadRequest("Du kan inte bokföra det här utlägget än")

    expense.verification = request.POST['verification']
    expense.save()

    comment = Comment(
        author=request.user.profile,
        expense=expense,
        content="Bokförde med verifikationsnumret: " + expense.verification
    )
    comment.save()

    return HttpResponseRedirect(reverse('expenses-action-account'))
        

"""
Lists all expenses.
"""
@require_GET
@login_required
@user_passes_test(lambda u: u.profile.is_admin())
def expense_overview(request):
    committee = request.GET.get('committee')
    expenses_list = Expense.objects.order_by('verification', '-id')
    if committee != None and committee != '':
        expenses_list = expenses_list.filter(expensepart__committee_name=committee)
    expenses_list = expenses_list.all()
    paginator = Paginator(expenses_list, 25)
    page = request.GET.get('page')

    try: expenses = paginator.page(page)
    except PageNotAnInteger: expenses = paginator.page(1)
    except EmptyPage: expenses = paginator.page(paginator.num_pages)

    return render(request, 'admin/expenses/overview.html', {
        'expenses': expenses,
        'committees': json.dumps([x['committee_name'] for x in ExpensePart.objects.values('committee_name').distinct()]),
        'committee': committee if committee != None else ''
    })

"""
Lists all users.
"""
@require_GET
@login_required
@user_passes_test(lambda u: u.profile.is_admin())
def user_overview(request):
    paginator = Paginator(Profile.objects.order_by('-id').all(), 25)
    page = request.GET.get('page')

    try: users = paginator.page(page)
    except PageNotAnInteger: users = paginator.page(1)
    except EmptyPage: users = paginator.page(paginator.num_pages)

    return render(request, 'admin/users/overview.html', {
        'users': users
    })

"""
Lists all invoices.
"""
@require_GET
@login_required
@user_passes_test(lambda u: u.profile.is_admin())
def invoice_overview(request):
    committee = request.GET.get('committee')
    invoices_list = Invoice.objects.order_by('verification', '-id')
    if committee != None and committee != '':
        invoices_list = invoices_list.filter(invoicepart__committee_name=committee)
    invoices_list = invoices_list.all()
    paginator = Paginator(invoices_list, 25)
    page = request.GET.get('page')

    try: invoices = paginator.page(page)
    except PageNotAnInteger: invoices = paginator.page(1)
    except EmptyPage: invoices = paginator.page(paginator.num_pages)

    return render(request, 'admin/invoices/overview.html', {
        'invoices': invoices,
        'committees': json.dumps([x['committee_name'] for x in ExpensePart.objects.values('committee_name').distinct()]),
        'committee': committee if committee != None else ''
    })












class fakefloat(float):
    def __init__(self, value):
        self._value = value
    def __repr__(self):
        return str(self._value)

def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return fakefloat(obj)
    raise TypeError ("Type %s not serializable" % type(obj))