from django.http import Http404, JsonResponse
from expenses.models import Expense, ExpensePart
from django.forms.models import model_to_dict


def expense(request, expense_id):
    if request.method != 'GET':
        raise Http404()

    try:
        expense_id = int(expense_id)
    except ValueError:
        raise Http404()
    exp = Expense.objects.get(id=expense_id)
    exp_dict = model_to_dict(exp)
    exp_dict['owner_username'] = exp.owner.user.username
    exp_dict['parts'] = []

    for expense_part in ExpensePart.objects.filter(expense=exp.id).all():
        partDict = model_to_dict(expense_part)
        partDict['budget_line'] = expense_part.budget_line.to_dict()
        exp_dict['parts'].append(partDict)

    return JsonResponse({'expense': exp_dict}, status=200, safe=False)


def expenses(request):
    if request.method != 'GET':
        raise Http404()
    return JsonResponse({'expenses': list(Expense.objects.all().values())})
