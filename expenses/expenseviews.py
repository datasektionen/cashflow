from django.http import Http404, JsonResponse
from expenses.models import Expense
from django.forms.models import model_to_dict


def expense(request, expense_id):

    try:
        expense_id = int(expense_id)
    except ValueError:
        raise Http404()
    exp = Expense.objects.get(id=expense_id)

    return JsonResponse({'expense': model_to_dict(exp)}, status=200, safe=False)


def expenses(request):
    if request.method != 'GET':
        raise Http404()
    return JsonResponse({'expenses': list(Expense.objects.all().values())})
