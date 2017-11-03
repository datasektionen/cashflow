from django.core.exceptions import ObjectDoesNotExist
from django.forms import modelform_factory
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse

from cashflow import dauth
from cashflow.dauth import has_permission
from expenses import models


def user_list(request):
    if request.method == 'GET':
        if len(dauth.get_permissions(request.user)) > 0:
            return render(request, 'expenses/user_list.html', {
                'users': models.Profile.objects.order_by('-id').all()
            })
    else:
        raise Http404()


def get_user(request, username):
    try:
        user = models.User.objects.get_by_natural_key(username)
        if not may_view_user(request, user):
            return HttpResponseForbidden()

        return render(request, 'expenses/user_information.html', {
            'showuser': user
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
    UserForm = modelform_factory(models.Profile,
                                 fields=('bank_account', 'sorting_number', 'bank_name', 'default_account'))
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
