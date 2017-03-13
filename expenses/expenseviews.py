from django.http import Http404, JsonResponse, HttpResponseBadRequest, HttpResponse, HttpResponseForbidden
from expenses.models import Expense, ExpensePart, Person
from datetime import date
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from cashflow.dauth import has_permission
import json


def expense(request, expense_id):
    try:
        expense_id = int(expense_id)
    except ValueError:
        raise Http404()

    try:
        exp = Expense.objects.get(id=expense_id)
    except ObjectDoesNotExist:
        raise Http404()

    if not (exp.owner.user is request.user or may_edit_expense(exp,request.user)):
        return HttpResponseForbidden()

    if request.method == 'GET':
        return JsonResponse({'expense': exp.to_dict()})

    elif request.method == 'PUT': # update the expense
        parts_to_save = []

        if not 'json' in request.PUT:
            return HttpResponseBadRequest()

        arg_dict = json.loads(request.PUT['json'])

        # Update provided fields
        if 'expense_date' in arg_dict:
            exp.expense_date = date(arg_dict['expense_date'])
        if 'description' in arg_dict:
            exp.description = date(arg_dict['description'])
        if 'expense_parts' in arg_dict:
            for part in arg_dict['expense_parts']:
                if 'id' in part:
                    # update already existing part
                    try:
                        exp_part = ExpensePart.objects.get(id=part['id'])
                    except ObjectDoesNotExist:
                        return HttpResponseBadRequest("Expense_part with id " + str(part['id']) + " does not exist!")

                    if exp_part.expense_id != exp.id:
                        return HttpResponseBadRequest("Expense_part with id " + str(part['id']) + " does not belong to that expense!")
                    if 'budget_line_id' in part:
                        exp_part.budget_line_id = part['budget_line_id']
                    if 'amount' in part:
                        exp_part.amount = part['amount']
                else:
                    try:
                        exp_part = ExpensePart(expense=exp,budget_line_id=part['budget_line_id'],amount=part['amount'])
                    except KeyError:
                        return HttpResponseBadRequest("The following expensepart was badly formated: \n" + json.dumps(part))
                parts_to_save.append(exp_part)
        for part in parts_to_save:
            part.save()
    else:
        return HttpResponse(status=501, content= request.method  + " is not a valid method to access resource!")


def expenses(request):
    if request.method == 'GET':
        return JsonResponse({'expenses': [expense.to_dict() for expense in Expense.objects.all()]})
    else:
        return HttpResponse(status=501, content= request.method  + " is not a valid method to access resource!")


def expenses_for_person(request, username):

    if request.method == 'GET':
        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            raise Http404()
        return JsonResponse({'expenses': [expense.to_dict() for expense in Expense.objects.filter(owner__user=user)]})
    else:
        return HttpResponse(status=501, content= request.method  + " is not a valid method to access resource!")


# Helper method
def may_edit_expense(exp,user):
    if has_permission("attest-*",user):
        return True

    for part in ExpensePart.objects.filter(expense=exp):
        if has_permission("attest-" + part.budget_line.cost_centre.committee.name, user):
            return True

    return False

