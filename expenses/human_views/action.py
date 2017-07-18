from django.shortcuts import render

from expenses import models


def attest_overview(request):
    may_attest = request.user.profile.may_attest()

    may_attest_committees = [models.Committee.objects.get(name__iexact=committee) for committee in may_attest]

    return render(request, 'expenses/action_attest.html', {
        'attestable_expenses': models.Expense.objects.exclude(owner__user=request.user).filter(
            expensepart__attested_by=None,
            expensepart__budget_line__cost_centre__committee__in=may_attest_committees
        ).distinct()
    })


def accounting_overview(request):
    may_account = request.user.profile.may_attest()

    may_account_committees = [models.Committee.objects.get(name__iexact=committee) for committee in may_account]

    return render(request, 'expenses/action_accounting.html', {
        'accounting_ready_expenses': models.Expense.objects.exclude(reimbursement=None).filter(
            verification="",
            expensepart__budget_line__cost_centre__committee__in=may_account_committees
        ).distinct()
    })
