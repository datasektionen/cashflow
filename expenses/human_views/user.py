from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse

from cashflow.dauth import has_permission
from expenses import models
from expenses.forms import UserForm


def get_user(request, username):
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

        return render(request, 'expenses/user.html',
                      {
                          'showuser': user,
                          'non_attested_expenses': non_attested_expenses,
                          'attested_expenses': attested_expenses,
                          'reimbursements': user.profile.receiver.all()
                      })
    except ObjectDoesNotExist:
        raise Http404("Användaren finns inte")


def edit_user(request, username):
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
