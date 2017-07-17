import json
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from expenses import models


def new_expense(request):
    if request.method == 'GET':

        return render(request, 'expenses/new_expense.html', {
            "committees": models.Committee.objects.order_by('name'),
            "budget_json": models.get_budget_json()

        })
    elif request.method == 'POST':
        expense = models.Expense(
            owner=request.user.profile,
            expense_date=request.POST['expense-date'],
            description=request.POST['expense-description'])
        expense.save()

        for uploaded_file in request.FILES.getlist('files'):
            file = models.File(belonging_to=expense, file=uploaded_file)
            file.save()

        expense_part_indices = json.loads(request.POST['expense_part_indices'])
        for i in expense_part_indices:
            expense_part = models.ExpensePart(
                expense=expense,
                budget_line=models.BudgetLine.objects.get(
                    cost_centre__committee__name=request.POST['expense_part-{}-committee'.format(i)],
                    cost_centre__name=request.POST['expense_part-{}-cost_centre'.format(i)],
                    name=request.POST['expense_part-{}-budget_line'.format(i)]
                ),
                amount=request.POST['expense_part-{}-amount'.format(i)]
            )
            expense_part.save()

        return HttpResponseRedirect(reverse('expenses-expense', kwargs={'pk': expense.id}))
    else:
        raise Http404()


def get_expense(request, pk):
    # TODO: Only let certain users view expense
    try:
        pk = int(pk)
        expense = models.Expense.objects.get(id=pk)

        return render(request, 'expenses/expense.html', {
            'expense': expense
        })
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")


def new_comment(request, expense_pk):
    if request.method == 'POST':
        comment = models.Comment(
            expense_id=int(expense_pk),
            date=datetime.now(),
            author=request.user.profile,
            content=request.POST['content']
        )
        comment.save()
        return HttpResponseRedirect(reverse('expenses-expense', kwargs={'pk': expense_pk}))
    else:
        raise Http404()
