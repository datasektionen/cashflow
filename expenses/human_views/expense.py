import json

from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render

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

        file = models.File(belonging_to=expense, file=request.FILES['files'])
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

        return HttpResponseRedirect("")
    else:
        raise Http404()
