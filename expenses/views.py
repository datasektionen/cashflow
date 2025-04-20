from datetime import datetime
import re
import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import Http404, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_GET, require_POST

from expenses import models

@require_http_methods(["GET", "POST"])
@login_required
def new_expense(request):
    """
    Add a new expense.
    """
    if request.method == 'GET':
        return render(request, 'expenses/new.html', {'budget_url': settings.BUDGET_URL})

    if len((request.FILES.getlist('files'))) < 1 and len((request.POST.getlist('fileIds[]'))) < 1:
        messages.error(request, 'Du måste ladda upp minst en fil som verifikat')
        return HttpResponseRedirect(reverse('expenses-new'))

    if datetime.now() < datetime.strptime(request.POST['expense-date'], '%Y-%m-%d'):
        messages.error(request, 'Du har angivit ett datum i framtiden')
        return HttpResponseRedirect(reverse('expenses-new'))

    if any(map(lambda x: float(x) <= 0, request.POST.getlist('amounts[]'))) > 0:
        messages.error(request, 'Du har angivit en icke-positiv summa i någon av kvittodelarna')
        return HttpResponseRedirect(reverse('expenses-new'))

    if len(request.POST.getlist('amounts[]')) == 0:
        messages.error(request, 'Du måste lägga till minst en del på kvittot')
        return HttpResponseRedirect(reverse('expenses-new'))

    with transaction.atomic():
        expense = models.Expense(
            owner=request.user.profile,
            expense_date=request.POST['expense-date'],
            description=request.POST['expense-description'].strip(),
            confirmed_by=None,
            is_digital='is-digital' in request.POST,
        )
        expense.save()

        # Add the files submitted
        for posted_file in request.FILES.getlist('files'):
            file = models.File(expense=expense, file=posted_file)
            file.save()

        # Add the files submitted to the javascript upload
        for pre_uploaded_file_id in request.POST.getlist('fileIds[]'):
            file = models.File.objects.get(pk=int(pre_uploaded_file_id))
            if file.expense is None:
                file.expense = expense
            file.save()

        # Add the expense parts
        for cost_centre, secondary_cost_centre, budget_line, amount in zip(
            request.POST.getlist("costCentres[]"),
            request.POST.getlist("secondaryCostCentres[]"),
            request.POST.getlist("budgetLines[]"),
            request.POST.getlist("amounts[]"),
        ):
            models.ExpensePart(
                expense=expense,
                cost_centre=cost_centre.split(",")[1],
                secondary_cost_centre=secondary_cost_centre.split(",")[1],
                budget_line=budget_line.split(",")[1],
                amount=amount,
            ).save()

    return HttpResponseRedirect(reverse('expenses-new-confirmation', kwargs={'pk': expense.id}))


@require_GET
@login_required
def expense_new_confirmation(request, pk):
    """
    Shows a confirmation of the new expense and tells user to put receipt into binder.
    """
    try:
        expense = models.Expense.objects.get(pk=int(pk))
    except ObjectDoesNotExist:
        messages.error(request, 'Ett fel uppstod och kvittot skapades inte.')
        return HttpResponseRedirect(reverse('expenses-new'))

    return render(request, 'expenses/confirmation.html', {'expense': expense})


@login_required
@require_http_methods(["GET", "POST"])
def edit_expense(request, pk):
    """
    Shows form for editing expense.
    """

    try:
        expense = models.Expense.objects.get(pk=pk)
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")

    if expense.reimbursement:
        messages.error(request, 'Kan inte ändra utlägg som har blivit utbetald')
        return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk': pk}))

    if expense.owner.user.username != request.user.username:
        messages.error(request, 'Kan inte ändra på någon annans utlägg')
        return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk': pk}))

    # Show the form on GET, otherwise handle as POST
    if request.method == 'GET':
        return render(request, 'expenses/edit.html', {
            "expense": expense,
            "expenseparts": expense.expensepart_set.all(),
            "budget_url": settings.BUDGET_URL,
        })

    expense.description = request.POST['description']
    expense.expense_date = request.POST['expense_date']
    expense.is_digital = 'is-digital' in request.POST
    if expense.is_flagged != None:
        expense.is_flagged = False

    expense.save()

    new_ids = []

    for cost_centre, secondary_cost_centre, budget_line, amount in zip(
        request.POST.getlist("costCentres[]"),
        request.POST.getlist("secondaryCostCentres[]"),
        request.POST.getlist("budgetLines[]"),
        request.POST.getlist("amounts[]"),
    ):
        if float(amount) < 1:
            messages.error(request, 'En budgetpost innehåller en felaktig summa och kunde därför inte sparas')
            continue

        expense_part = models.ExpensePart(
            expense=expense,
            cost_centre=cost_centre.split(",")[1],
            secondary_cost_centre=secondary_cost_centre.split(",")[1],
            budget_line=budget_line.split(",")[1],
            amount=amount,
        )
        expense_part.save()
        new_ids.append(expense_part.id)

    if len(new_ids) < 1:
        messages.warning(request, 'Något gick fel med inladdning av budgetposterna')
        return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk': pk}))

    models.ExpensePart.objects.filter(expense=expense).exclude(id__in=new_ids).delete()

    messages.success(request, 'Kvittot ändrades')

    return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk': pk}))


@require_http_methods(["GET", "POST"])
@login_required
def delete_expense(request, pk):
    """
    Delete expense. Ask for confirmation on GET and send to POST.
    """
    try:
        expense = models.Expense.objects.get(pk=pk)
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")

    if not request.user.profile.may_delete(expense):
        return HttpResponseForbidden('Du har inte behörighet att ta bort detta kvitto.')
    if expense.reimbursement is not None:
        return HttpResponseBadRequest('Du kan inte ta bort ett kvitto som är återbetalt!')

    if request.method == 'GET':
        return render(request, 'expenses/delete.html', {"expense": expense})
    if request.method == 'POST':
        # Will be removed, but sends an email
        models.Comment(
            author=request.user.profile,
            expense=expense,
            content="Raderade utlägg " + str(expense.id),
        ).save()
        expense.delete()
        messages.success(request, 'Kvittot raderades.')
        return HttpResponseRedirect(reverse('expenses-index'))

@require_POST
@login_required
@user_passes_test(lambda u: u.profile.may_flag())
def flag_expense(request, pk):
    """
    Flag a problematic expense
    """ 
    try:
        expense = models.Expense.objects.get(pk=pk)
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")
    expense.is_flagged = True
    expense.save()
    return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk': int(pk)}))


@require_GET
@login_required
def get_expense(request, pk):
    """
    Shows one expense.
    """
    try:
        expense = models.Expense.objects.get(pk=int(pk))
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")

    if not request.user.profile.may_view_expense(expense):
        return HttpResponseForbidden()

    attestable = []
    for expense_part in expense.expensepart_set.all():
        if request.user.profile.may_attest(expense_part):
            attestable.append(expense_part.id)

    return render(request, 'expenses/show.html', {
        'expense': expense,
        'may_account': request.user.profile.may_account(),
        'may_unattest': request.user.profile.may_unattest() and not expense.reimbursement,
        'may_flag': request.user.profile.may_flag(),
        'attestable': attestable,
        'may_delete': request.user.profile.may_delete(expense),
    })


@require_POST
@login_required
def new_comment(request, expense_pk):
    """
    Adds new comment to receipt.
    """
    try:
        expense = models.Expense.objects.get(pk=int(expense_pk))
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")

    if not request.user.profile.may_view_expense(expense):
        return HttpResponseForbidden()
    if re.match('^\s*$', request.POST['content']):
        return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk': expense_pk}))

    models.Comment(
        expense=expense,
        author=request.user.profile,
        content=request.POST['content']
    ).save()

    return HttpResponseRedirect(reverse('expenses-show', kwargs={'pk': expense_pk}))


def index(request):
    """
    Displays an index page.
    """
    return render(request, 'index.html')


def get_payment(request, pk):
    try:
        payment = models.Payment.objects.get(pk=pk)

        return render(request, 'expenses/payment.html', {
            'payment': payment
        })
    except ObjectDoesNotExist:
        raise Http404("Utbetalningen finns inte")


@login_required
@require_POST
@user_passes_test(lambda u: u.profile.may_pay())
def new_payment(request):
    """
    Performs a payment
    """
    try:
        expenses = [models.Expense.objects.get(id=int(expense_id)) for expense_id in request.POST.getlist('expense')]
    except ObjectDoesNotExist:
        raise Http404("Ett av utläggen finns inte.")

    expense_owner = expenses[0].owner
    for expense in expenses:
        if expense.owner != expense_owner:
            return HttpResponseBadRequest("Alla kvitton måste ha samma ägare")

    if expense_owner.bank_name == "" or expense_owner.bank_account == "" or expense_owner.sorting_number == "":
        return HttpResponseBadRequest("Användaren har inte angett alla sina bankuppgifter")

    payment = models.Payment(
        payer=request.user.profile,
        receiver=expense_owner,
        account=models.BankAccount.objects.get(name=request.POST['account'])
    )
    payment.save()

    for expense in expenses:
        expense.reimbursement = payment
        expense.save()

        models.Comment(
            author=request.user.profile,
            expense=expense,
            content="Betalade ut i betalning " + str(payment.id)
        ).save()

    return HttpResponseRedirect(reverse('expenses-action-pay') + "?payment=" + str(payment.id))


@login_required
@require_POST
@user_passes_test(lambda u: u.profile.may_pay())
def api_new_payment(request):
    try:
        expenses = [models.Expense.objects.get(id=int(expense_id)) for expense_id in request.POST.getlist('expense')]
    except ObjectDoesNotExist:
        raise Http404("Ett av utläggen finns inte.")

    for expense in expenses:
        if expense.reimbursement:
            return HttpResponseBadRequest("Något utlägg är redan utbetalat")

    expense_owner = expenses[0].owner
    for expense in expenses:
        if expense.owner != expense_owner:
            return HttpResponseBadRequest("Alla kvitton måste ha samma ägare")

    if expense_owner.bank_name == "" or expense_owner.bank_account == "" or expense_owner.sorting_number == "":
        return HttpResponseBadRequest("Användaren har inte angett alla sina bankuppgifter")

    payment = models.Payment(
        payer=request.user.profile,
        receiver=expense_owner,
        account=models.BankAccount.objects.get(name=request.POST['account'])
    )
    payment.save()

    for expense in expenses:
        expense.reimbursement = payment
        expense.save()

        models.Comment(
            author=request.user.profile,
            expense=expense,
            content="Betalade ut i betalning " + str(payment.id)
        ).save()

    return JsonResponse({
        'payment': payment.to_dict(),
        'expenses': [e.to_dict() for e in expenses]
    })
