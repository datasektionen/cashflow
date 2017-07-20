from django.http import HttpResponseForbidden
from django.shortcuts import render

from cashflow import dauth
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


def pay_overview(request):
    if not dauth.has_permission('pay', request):
        return HttpResponseForbidden("Du har inte rättigheterna för att se den här sidan")

    context = {
        'payable_expenses': models.Expense.objects.filter(reimbursement=None)
            .exclude(expensepart__attested_by=None).order_by('owner__user__username'),
        'accounts': models.BankAccount.objects.all().order_by('name')}

    if request.GET:
        context['payment'] = models.Payment.objects.get(id=int(request.GET['payment']))

    return render(request, 'expenses/action_pay.html', context)


def accounting_overview(request):
    may_account = request.user.profile.may_attest()

    may_account_committees = [models.Committee.objects.get(name__iexact=committee) for committee in may_account]

    return render(request, 'expenses/action_accounting.html', {
        'accounting_ready_expenses': models.Expense.objects.exclude(reimbursement=None).filter(
            verification="",
            expensepart__budget_line__cost_centre__committee__in=may_account_committees
        ).distinct()
    })
