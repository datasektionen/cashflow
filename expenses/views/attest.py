import json
from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse, HttpResponseForbidden

from cashflow.dauth import has_permission
from expenses.models import Expense, ExpensePart, Person


def attest(request):
    if request.method == 'GET':
        expenses__to_attest = []

        # Add all expenses that the user may attest
        for expense in Expense.objects.filter(expensepart__attested_by__isnull=True).distinct():
            if may_attest_expense(expense, request.user):
                expenses__to_attest.append(expense.to_dict())

        return JsonResponse({
            'Expenses': expenses__to_attest
        })
    elif request.method == 'POST':
        expense_parts_to_be_saved = []
        if 'json' not in request.POST:
            return HttpResponseBadRequest()

        expense_part_ids = json.loads(request.POST['json'])

        for exp_part_id in expense_part_ids:
            try:
                part = ExpensePart.objects.get(id=exp_part_id)
            except ObjectDoesNotExist as e:
                return HttpResponseBadRequest(content="Expense_part with id " + str(e) + " does not exist")

            if has_permission("attest-*", request.user) or \
                    has_permission("attest-" + part.budget_line.cost_centre.committee.name, request.user):

                if part.attested_by is None:
                    part.attested_by = Person.objects.get(user=request.user)
                    part.attest_date = date.today()
                    expense_parts_to_be_saved.append(part)
            else:
                return HttpResponseForbidden()
        for part in expense_parts_to_be_saved:
            part.save()

        return HttpResponse("SUCCESS!")
    else:
        return HttpResponse(status=501, content=request.method + " is not a valid method to access resource!")


# Helper method
def may_attest_expense(exp, user):
    if has_permission("attest-*", user):
        return True

    for part in ExpensePart.objects.filter(expense=exp):
        if has_permission("attest-" + part.budget_line.cost_centre.committee.name, user):
            return True

    return False
