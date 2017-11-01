import json
import re

from django.core.exceptions import ObjectDoesNotExist
from django.forms import modelform_factory
from django.http import Http404, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden, \
    HttpResponseServerError
from django.shortcuts import render
from django.urls import reverse

from cashflow import dauth
from expenses import models


def expense_overview(request):
    if request.method == 'GET':
        if len(dauth.get_permissions(request.user)) > 0:
            return render(request, 'expenses/expense_list.html', {
                'expenses': models.Expense.objects.order_by('-id').all()
            })
    else:
        raise Http404()


def new_expense(request):
    if request.method == 'GET':
        return render(request, 'expenses/new_expense.html')
    elif request.method == 'POST':
        if len((request.FILES.getlist('files'))) < 1:
            return HttpResponseBadRequest("Du måste ladda upp minst en fil som verifikat")

        expense = models.Expense(
            owner=request.user.profile,
            expense_date=request.POST['expense-date'],
            description=request.POST['expense-description'])
        expense.save()

        for uploaded_file in request.FILES.getlist('files'):
            file = models.File(belonging_to=expense, file=uploaded_file)
            file.save()

        for idx, budgetLineId in enumerate(request.POST.getlist('budgetLine[]')):
            print(expense)
            print(budgetLineId)
            print(request.POST.getlist('amount[]')[idx])
            expense_part = models.ExpensePart(
                expense=expense,
                budget_line_id=budgetLineId,
                amount=request.POST.getlist('amount[]')[idx]
            )
            expense_part.save()

        return HttpResponseRedirect(reverse('expenses-expense-new-binder', kwargs={'pk': expense.id}))
    else:
        raise Http404()


def expense_in_binder_alert(request, pk):
    if request.method == 'GET':
        try:
            expense = models.Expense.objects.get(pk=int(pk))

            return render(request, 'expenses/expense_in_binder.html', {'expense': expense})
        except ObjectDoesNotExist:
            return HttpResponseServerError("Något gick fel när du försökte skapa kvittot :(")

    else:
        raise Http404()


def edit_expense(request, pk):
    ExpenseForm = modelform_factory(models.Expense,
                                    fields=('description', 'expense_date'))
    try:
        expense = models.Expense.objects.get(pk=pk)
        if expense.owner.user.username != request.user.username:
            return HttpResponseForbidden()
        if request.method == 'POST':
            received_form = ExpenseForm(request.POST, instance=expense)
            if received_form.is_valid():
                received_form.save()
                return HttpResponseRedirect(reverse('expenses-expense', kwargs={'pk': pk}))
        else:

            return render(request, 'expenses/edit_expense.html', {
                "form": ExpenseForm(instance=expense)
            })
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")


def delete_expense(request, pk):
    try:
        expense = models.Expense.objects.get(pk=pk)
        if expense.owner.user.username != request.user.username and not(expense.expensepart_set.first().budget_line.cost_centre.committee.name.lower() in request.user.profile.may_attest()):
            return HttpResponseForbidden()
        if request.method == 'GET':
            return render(request, 'expenses/delete_expense.html', {
                "expense": expense
            })
        if request.method == 'POST':
            if expense.reimbursement is not None:
                return HttpResponseBadRequest('Du kan inte ta bort ett kvitto som är återbetalt!')
            expense.delete()
            return HttpResponseRedirect(reverse('expenses-index'))

    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")


def get_expense(request, pk):
    try:
        pk = int(pk)
        expense = models.Expense.objects.get(pk=pk)

        if not may_view_expense(request, expense):
            return HttpResponseForbidden()

        return render(request, 'expenses/expense.html', {
            'expense': expense
        })
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")


def new_comment(request, expense_pk):
    try:
        expense = models.Expense.objects.get(pk=int(expense_pk))
        if not may_view_expense(request, expense):
            return HttpResponseForbidden()

        if request.method == 'POST':
            if re.match('^\s*$', request.POST['content']):
                return HttpResponseRedirect(reverse('expenses-expense', kwargs={'pk': expense_pk}))
            comment = models.Comment(
                expense=expense,
                author=request.user.profile,
                content=request.POST['content']
            )
            comment.save()
            return HttpResponseRedirect(reverse('expenses-expense', kwargs={'pk': expense_pk}))
        else:
            raise Http404()
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")


def set_verification(request, expense_pk):
    if request.method == 'POST':
        try:
            expense = models.Expense.objects.get(pk=expense_pk)
            if not may_account(request, expense):
                return HttpResponseForbidden("Du har inte rättigheter att bokföra det här")
            if expense.reimbursement is None:
                return HttpResponseBadRequest("Du kan inte bokföra det här utlägget än")

            expense.verification = request.POST['verification']
            expense.save()

            return HttpResponseRedirect(reverse('expenses-action-accounting'))
        except ObjectDoesNotExist:
            raise Http404("Utlägget finns inte")
    else:
        raise Http404()


def may_view_expense(request, expense):
    if expense.owner.user.username == request.user.username or dauth.has_permission('pay', request):
        return True
    for committee in expense.committees():
        if dauth.has_permission('attest-' + committee.name.lower(), request) or \
                dauth.has_permission('accounting-' + committee.name.lower(), request):
            return True

    return False


def may_account(request, expense):
    for committee in expense.committees():
        if committee.name.lower() in request.user.profile.may_account():
            return True

    return False
