from django.http import Http404, JsonResponse
from expenses import models


def expense(request, expense_id):

    try:
        expense_id = int(expense_id)
    except ValueError:
        raise Http404()
    exp = models.Expense.objects.get(id=expense_id)

    return JsonResponse({'expense': list(exp)}, status=200, safe=False)


def expenses(request):
    if request.method != 'GET':
        raise Http404()
    return JsonResponse({'expenses': list(models.Expense.objects.all())})
