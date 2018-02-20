from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseServerError, JsonResponse
from django.shortcuts import render
from django.core import serializers
from django.forms.models import model_to_dict
from datetime import date, datetime
from decimal import *
from django.contrib import messages
import re
import json
import requests
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods, require_GET, require_POST

from cashflow import dauth
from expenses import models

"""
Add a new expense.
"""
@require_http_methods(["GET", "POST"])
@login_required
def new_expense(request):
    if request.method == 'GET': return render(request, 'expenses/new.html')
    elif request.method == 'POST':
        # Validate
        if len((request.FILES.getlist('files'))) < 1:
            messages.error(request, 'Du måste ladda upp minst en fil som verifikat')
            return HttpResponseRedirect(reverse('expenses-new'))

        if datetime.now() < datetime.strptime(request.POST['expense-date'], '%Y-%m-%d'):
            messages.error(request, 'Du har angivit ett datum i framtiden')
            return HttpResponseRedirect(reverse('expenses-new'))

        # Create the expense
        expense = models.Expense(
            owner=request.user.profile,
            expense_date=request.POST['expense-date'],
            description=request.POST['expense-description'],
            confirmed_by=None
        )
        expense.save()

        # Add the file
        for uploaded_file in request.FILES.getlist('files'):
            file = models.File(expense=expense, file=uploaded_file)
            file.save()

        # Add the expenseparts
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

        return HttpResponseRedirect(reverse('expenses-new-confirmation', kwargs={'pk': expense.id}))

"""
Shows a confirmation of the new expense and tells user to put receipt into binder.
"""
@require_GET
@login_required
def expense_new_confirmation(request, pk):
    try: expense = models.Expense.objects.get(pk=int(pk))
    except ObjectDoesNotExist:
        messages.error(request, 'Ett fel uppstod och kvittot skapades inte.')
        return HttpResponseRedirect(reverse('expenses-new'))

    return render(request, 'expenses/confirmation.html', {'expense': expense})

"""
Shows form for editing expense.
"""
@login_required
@require_http_methods(["GET", "POST"])
def edit_expense(request, pk):
    try: expense = models.Expense.objects.get(pk=pk)
    except ObjectDoesNotExist: raise Http404("Utlägget finns inte")

    if expense.owner.user.username != request.user.username: return HttpResponseForbidden()

    # Show the form on GET, otherwise handle as POST
    if request.method == 'GET':
        return render(request, 'expenses/edit.html', {
            "expense": expense,
            "expenseparts": expense.expensepart_set.all()
        })

    expense.description = request.POST['description']
    expense.expense_date = request.POST['expense_date']
    expense.save()

    newIds = []
    for idx, expensePartId in enumerate(request.POST.getlist('expensePartId[]')):
        budgetLines = request.POST.getlist('budgetLine[]')
        response = requests.get("https://budget.datasektionen.se/api/budget-lines/{}".format(budgetLines[idx]))
        budgetLine = response.json()

        if expensePartId == '-1':
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
            newIds.append(expense_part.id)
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
            newIds.append(expense_part.id)

    models.ExpensePart.objects.filter(expense=expense).exclude(id__in=newIds).delete()

    messages.success(request, 'Kvittot ändrades')

    return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk': pk}))

"""
Delete expense. Ask for confirmation on GET and send to POST.
"""
@require_http_methods(["GET", "POST"])
@login_required
def delete_expense(request, pk):
    try: expense = models.Expense.objects.get(pk=pk)
    except ObjectDoesNotExist: raise Http404("Utlägget finns inte")

    if not request.user.profile.may_delete(expense): return HttpResponseForbidden('Du har inte behörighet att ta bort detta kvitto.')
    if expense.reimbursement is not None: return HttpResponseBadRequest('Du kan inte ta bort ett kvitto som är återbetalt!')

    if request.method == 'GET': return render(request, 'expenses/delete.html', { "expense": expense })
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Kvittot raderades.')
        return HttpResponseRedirect(reverse('expenses-index'))

"""
Shows one expense.
"""
@require_GET
@login_required
def get_expense(request, pk):
    try: expense = models.Expense.objects.get(pk=int(pk))
    except ObjectDoesNotExist: raise Http404("Utlägget finns inte")

    if not request.user.profile.may_view_expense(expense): return HttpResponseForbidden()

    return render(request, 'expenses/show.html', {
        'expense': expense,
        'may_account': request.user.profile.may_account()
    })

"""
Adds new comment to receipt.
"""
@require_POST
@login_required
def new_comment(request, expense_pk):
    try: expense = models.Expense.objects.get(pk=int(expense_pk))
    except ObjectDoesNotExist: raise Http404("Utlägget finns inte")

    if not request.user.profile.may_view_expense(expense): return HttpResponseForbidden()
    if re.match('^\s*$', request.POST['content']): return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk': expense_pk}))
    
    models.Comment(
        expense=expense,
        author=request.user.profile,
        content=request.POST['content']
    ).save()

    return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk': expense_pk}))

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

"""
Performs a payment
"""
@login_required
@require_POST
@user_passes_test(lambda u: u.profile.may_pay())
def new_payment(request):
    try: expenses = [models.Expense.objects.get(id=int(expense_id)) for expense_id in request.POST.getlist('expense')]
    except ObjectDoesNotExist as e: raise Http404("Ett av utläggen finns inte.")

    expense_owner = expenses[0].owner
    for expense in expenses:
        if expense.owner != expense_owner:
            return HttpResponseBadRequest("Alla kvitton måste ha samma ägare")

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

        models.Comment(
            author=request.user.profile,
            expense=expense,
            content="Betalade ut i betalning " + payment.id
        ).save()

    return HttpResponseRedirect(reverse('expenses-action-pay') + "?payment=" + str(payment.id))

@login_required
@require_POST
@user_passes_test(lambda u: u.profile.may_pay())
def api_new_payment(request):
    try: expenses = [models.Expense.objects.get(id=int(expense_id)) for expense_id in request.POST.getlist('expense')]
    except ObjectDoesNotExist as e: raise Http404("Ett av utläggen finns inte.")
        
    expense_owner = expenses[0].owner
    for expense in expenses:
        if expense.owner != expense_owner:
            return HttpResponseBadRequest("Alla kvitton måste ha samma ägare")

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

        models.Comment(
            author=request.user.profile,
            expense=expense,
            content="Betalade ut i betalning " + str(payment.id)
        ).save()

    return JsonResponse({
        'payment': payment.to_dict(), 
        'expenses': [e.to_dict() for e in expenses]
    })
