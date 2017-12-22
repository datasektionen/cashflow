from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden, \
    HttpResponseServerError
from django.shortcuts import render
from django.core import serializers
from django.forms.models import model_to_dict
from datetime import date, datetime
from decimal import *
import json
import requests
from django.urls import reverse

from cashflow import dauth
from expenses import models


def new_expense(request):
    if request.method == 'GET':
        return render(request, 'expenses/new_expense.html')
    elif request.method == 'POST':
        if len((request.FILES.getlist('files'))) < 1:
            messages.error(request, 'Du måste ladda upp minst en fil som verifikat')
            return HttpResponseRedirect(reverse('expenses-expense-new'))

        if datetime.now() < datetime.strptime(request.POST['expense-date'], '%Y-%m-%d'):
            messages.error(request, 'Du har angivit ett datum i framtiden')
            return HttpResponseRedirect(reverse('expenses-expense-new'))

        expense = models.Expense(
            owner=request.user.profile,
            expense_date=request.POST['expense-date'],
            description=request.POST['expense-description'],
            confirmed_by=None
        )
        expense.save()

        for uploaded_file in request.FILES.getlist('files'):
            file = models.File(belonging_to=expense, file=uploaded_file)
            file.save()

        for idx, budgetLineId in enumerate(request.POST.getlist('budgetLine[]')):
            response = requests.get("https://budget.datasektionen.se/api/budget-lines/{}".format(budgetLineId))
            budgetLine = response.json()
            models.ExpensePart(
                expense=expense,
                budget_line_id=budgetLine['id'],
                budget_line_name=budgetLine['name'],
                cost_centre_name=budgetLine['cost_centre']['name'],
                cost_centre_id=budgetLine['cost_centre']['id'],
                committee_name=budgetLine['cost_centre']['committee']['name'],
                committee_id=budgetLine['cost_centre']['committee']['id'],
                amount=request.POST.getlist('amount[]')[idx]
            ).save()

        return HttpResponseRedirect(reverse('expenses-expense-new-binder', kwargs={'pk': expense.id}))
    else:
        raise Http404()

def expense_in_binder_alert(request, pk):
    if request.method == 'GET':
        try:
            expense = models.Expense.objects.get(pk=int(pk))
            return render(request, 'expenses/expense_in_binder.html', {'expense': expense})
        except ObjectDoesNotExist:
            return HttpResponseServerError("Något gick fel när du försökte skapa utlägget :(")

    else:
        raise Http404()

def edit_expense(request, pk):
    try:
        expense = models.Expense.objects.get(pk=pk)
        if expense.owner.user.username != request.user.username:
            return HttpResponseForbidden()
        if request.method == 'POST':
            messages.success(request, 'Kvittot ändrades')
            expense.description = request.POST['description']
            expense.expense_date = request.POST['expense_date']
            expense.save()

            for idx, expensePartId in enumerate(request.POST.getlist('expensePartId[]')):
                budgetLines = request.POST.getlist('budgetLine[]')
                response = requests.get("https://budget.datasektionen.se/api/budget-lines/{}".format(budgetLines[idx]))
                budgetLine = response.json()

                if (expensePartId == '-1'):
                    expense_part = models.ExpensePart(
                        expense=expense,
                        budget_line_id=budgetLine['id'],
                        budget_line_name=budgetLine['name'],
                        cost_centre_name=budgetLine['cost_centre']['name'],
                        cost_centre_id=budgetLine['cost_centre']['id'],
                        committee_name=budgetLine['cost_centre']['committee']['name'],
                        committee_id=budgetLine['cost_centre']['committee']['id'],
                        amount=request.POST.getlist('amount[]')[idx]
                    )
                    expense_part.save()
                else:
                    expense_part = models.ExpensePart.objects.get(pk=expensePartId)
                    expense_part.expense = expense
                    expense_part.budget_line_id = budgetLine['id']
                    expense_part.budget_line_name = budgetLine['name']
                    expense_part.cost_centre_name = budgetLine['cost_centre']['name']
                    expense_part.cost_centre_id = budgetLine['cost_centre']['id']
                    expense_part.committee_name = budgetLine['cost_centre']['committee']['name']
                    expense_part.committee_id = budgetLine['cost_centre']['committee']['id']
                    expense_part.amount = request.POST.getlist('amount[]')[idx]
                    expense_part.save()

            return HttpResponseRedirect(reverse('expenses-expense', kwargs={'pk': pk}))
        else:
            return render(request, 'expenses/edit_expense.html', {
                "expense": expense,
                "expenseparts": expense.expensepart_set.all()
            })
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")

def delete_expense(request, pk):
    try:
        expense = models.Expense.objects.get(pk=pk)
        if expense.owner.user.username != request.user.username and not(expense.expensepart_set.first().budget_line.cost_centre.committee.name.lower() in request.user.profile.may_attest()):
            return HttpResponseForbidden()
        if request.method == 'GET':
            return render(request, 'expenses/delete_expense.html', {
                "expense": expense
            })
        if request.method == 'POST':
            if expense.reimbursement is not None:
                return HttpResponseBadRequest('Du kan inte ta bort ett kvitto som är återbetalt!')
            expense.delete()
            messages.success(request, 'Kvittot raderades.')
            return HttpResponseRedirect(reverse('expenses-index'))

    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")

def get_expense(request, pk):
    try:
        pk = int(pk)
        expense = models.Expense.objects.get(pk=pk)

        if not may_view_expense(request, expense):
            return HttpResponseForbidden()

        return render(request, 'expenses/expense.html', {
            'expense': expense,
            'may_account': may_account(request, expense)
        })
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")

def new_comment(request, expense_pk):
    try:
        expense = models.Expense.objects.get(pk=int(expense_pk))
        if not may_view_expense(request, expense):
            return HttpResponseForbidden()

        if request.method == 'POST':
            if re.match('^\s*$', request.POST['content']):
                return HttpResponseRedirect(reverse('expenses-expense', kwargs={'pk': expense_pk}))
            comment = models.Comment(
                expense=expense,
                author=request.user.profile,
                content=request.POST['content']
            )
            comment.save()
            return HttpResponseRedirect(reverse('expenses-expense', kwargs={'pk': expense_pk}))
        else:
            raise Http404()
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")




def may_view_expense(request, expense):
    if expense.owner.user.username == request.user.username or dauth.has_permission('pay', request):
        return True
    for committee in expense.committees():
        if dauth.has_permission('attest-' + committee.name.lower(), request) or \
                dauth.has_permission('accounting-' + committee.name.lower(), request):
            return True

    return False

def may_account(request, expense):
    for committee in expense.committees():
        if committee['committee_name'].lower() in request.user.profile.may_account():
            return True

    return False

"""
Displays an index page.
"""
def index(request):
    return render(request, 'index.html')

def get_payment(request, pk):
    try:
        payment = models.Payment.objects.get(pk=pk)

        return render(request, 'expenses/payment.html', {
            'payment': payment
        })
    except ObjectDoesNotExist:
        raise Http404("Utbetalningen finns inte")

def new_payment(request):
    if not has_permission('pay', request):
        return HttpResponseForbidden()

    if request.method == "POST":
        try:
            expenses = [
                models.Expense.objects.get(id=int(expense_id)) for expense_id in request.POST.getlist('expense')
            ]

            expense_owner = expenses[0].owner
            for expense in expenses:
                if expense.owner != expense_owner:
                    return HttpResponseBadRequest("Alla kvitton måste ha samma ägare")

        except ObjectDoesNotExist as e:
            raise Http404("Ett av utläggen finns inte.")
        if expense_owner.bank_name == "" or expense_owner.bank_account == "" or expense_owner.sorting_number == "":
            return HttpResponseServerError("Användaren har inte angett alla sina bankuppgifter")
        payment = models.Payment(
            payer=request.user.profile,
            receiver=expense_owner,
            account=models.BankAccount.objects.get(name=request.POST['account'])
        )
        payment.save()
        for expense in expenses:
            expense.reimbursement = payment
            expense.save()
        return HttpResponseRedirect(reverse('expenses-action-pay') + "?payment=" + str(payment.id))
    else:
        raise Http404()

def api_new_payment(request):
    if not has_permission('pay', request):
        return HttpResponseForbidden()

    if request.method == "POST":
        try:
            expenses = [models.Expense.objects.get(id=int(expense_id)) for expense_id in request.POST.getlist('expense')]
            expense_owner = expenses[0].owner
            for expense in expenses:
                if expense.owner != expense_owner:
                    return HttpResponseBadRequest("Alla kvitton måste ha samma ägare")

        except ObjectDoesNotExist as e:
            raise Http404("Ett av utläggen finns inte.")
        if expense_owner.bank_name == "" or expense_owner.bank_account == "" or expense_owner.sorting_number == "":
            return HttpResponseServerError("Användaren har inte angett alla sina bankuppgifter")
        payment = models.Payment(
            payer=request.user.profile,
            receiver=expense_owner,
            account=models.BankAccount.objects.get(name=request.POST['account'])
        )
        payment.save()
        for expense in expenses:
            expense.reimbursement = payment
            expense.save()
        return JsonResponse({'payment':payment.to_dict(), 'expenses':[e.to_dict() for e in expenses]})
    else:
        raise Http404()

def get_user(request, username):
    try:
        user = models.User.objects.get_by_natural_key(username)
        if not may_view_user(request, user):
            return HttpResponseForbidden()

        return render(request, 'expenses/user_information.html', {
            'showuser': user,
            'total': models.ExpensePart.objects.filter(expense__owner=user.profile).aggregate(Sum('amount'))
        })
    except ObjectDoesNotExist:
        raise Http404("Användaren finns inte")

def get_user_receipts(request, username):
    try:
        user = models.User.objects.get_by_natural_key(username)
        if not may_view_user(request, user):
            return HttpResponseForbidden()

        non_attested_expenses = []
        attested_expenses = []

        for expense in user.profile.expense_set.all():
            if expense.reimbursement is not None:
                continue  # expense is waay past attesting

            for expense_part in expense.expensepart_set.all():
                if expense_part.attested_by is None:
                    non_attested_expenses.append(expense)
                    break
            else:  # inner loop didn't break
                attested_expenses.append(expense)

        non_attested_expenses.sort(key=(lambda exp: exp.id), reverse=True)
        attested_expenses.sort(key=(lambda exp: exp.id), reverse=True)

        return render(request, 'expenses/user_receipts.html', {
            'showuser': user,
            'non_attested_expenses': non_attested_expenses,
            'attested_expenses': attested_expenses,
            'reimbursements': user.profile.receiver.all()
        })

    except ObjectDoesNotExist:
        raise Http404("Användaren finns inte")

def edit_user(request, username):
    # noinspection PyPep8Naming
    UserForm = modelform_factory(models.Profile, fields=('bank_account', 'sorting_number', 'bank_name', 'default_account'))
    try:
        user = models.User.objects.get_by_natural_key(username)
        if username != request.user.username:
            return HttpResponseForbidden()
        if request.method == 'POST':
            received_form = UserForm(request.POST, instance=user.profile)
            if received_form.is_valid():
                received_form.save()
                return HttpResponseRedirect(reverse('expenses-user', args=[username]))
        else:
            form = UserForm(instance=user.profile)
            return render(request, 'expenses/edit_user.html', {
                "form": form
            })
    except ObjectDoesNotExist:
        raise Http404("Användaren finns inte")

def may_view_user(request, user_to_view):
    return (request.user == user_to_view) or \
           has_permission('pay', request) or \
           (len(request.user.profile.may_account()) > 0)






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

