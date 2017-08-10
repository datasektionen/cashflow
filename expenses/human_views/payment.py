from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseForbidden, HttpResponseBadRequest, HttpResponseRedirect, \
    HttpResponseServerError
from django.shortcuts import render
from django.urls import reverse

from cashflow.dauth import has_permission
from expenses import models


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
