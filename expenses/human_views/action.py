from django.shortcuts import render

from expenses import models


def attest_overview(request):
    may_attest = request.user.profile.may_attest()
    may_attest_expenses = []
    for expense in models.Expense.objects.all():
        if expense.owner.user == request.user:
            continue
        for expense_part in expense.expensepart_set.all():
            if expense_part.budget_line.cost_centre.committee.name.lower() in may_attest and \
                            expense_part.attested_by is None:
                may_attest_expenses.append(expense)
                break

    return render(request, 'expenses/action_attest.html', {
        'attestable_expenses': may_attest_expenses
    })
