from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages
from expenses import models

"""
Shows form for editing expense part and handles the form submit.
"""
def edit_expense_part(request, pk):
    raise Http404('Det här är inte implementerat i Cashflow 3.0 än')
    
    try:
        expense_part = models.ExpensePart.objects.get(pk=int(pk))

        if request.user.username != expense_part.expense.owner.user.username:
            return HttpResponseForbidden("Endast kvittoägaren får redigera kvittodelarna")

        print(expense_part.amount)
        if request.method == 'GET':
            return render(request, 'expenses/edit_expense_part.html', {
                'expense_part': expense_part
            })
        elif request.method == 'POST':
            committee = request.POST['committee']
            cost_centre = request.POST['cost_centre']
            budget_line = request.POST['budget_line']

            original_str_repr = str(expense_part)

            expense_part.budget_line = models.BudgetLine.objects.get(
                cost_centre__committee__name=committee,
                cost_centre__name=cost_centre,
                name=budget_line)
            expense_part.amount = float(request.POST['amount'])

            expense_part.attested_by = None
            expense_part.attest_date = None

            expense_part.save()

            comment = models.Comment(
                author=request.user.profile,
                expense=expense_part.expense,
                content="Ändrade kvittodelen " + original_str_repr + " till " + str(expense_part)
            )
            comment.save()
            return HttpResponseRedirect(reverse('expenses-expense', kwargs={'pk': expense_part.expense.id}))
        else:
            raise Http404()

    except ObjectDoesNotExist:
        raise Http404("Kvittodelen finns inte")


"""
Handles attest action.
"""
def attest_expense_part(request, pk):
    try:
        expense_part = models.ExpensePart.objects.get(pk=int(pk))
        if request.method == 'POST':
            if request.user.username == expense_part.expense.owner.user.username:
                messages.error(request, 'Du kan inte attestera dina egna kvitton')
                return HttpResponseRedirect(reverse('expenses-expense', kwargs={'pk': expense_part.expense.id}))

            expense_part.attested_by = request.user.profile
            expense_part.attest_date = date.today()

            expense_part.save()
            comment = models.Comment(
                author=request.user.profile,
                expense=expense_part.expense,
                content="Attesterade kvittodelen: " + str(expense_part)
            )
            comment.save()
            return HttpResponseRedirect(reverse('expenses-expense', kwargs={'pk': expense_part.expense.id}))
        else:
            raise Http404()

    except ObjectDoesNotExist:
        raise Http404("Kvittodelen finns inte")
