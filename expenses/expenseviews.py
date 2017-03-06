from django.shortcuts import render
from django.http import Http404, JsonResponse, HttpResponse
from expenses import models
from django.core import serializers


def expense(request,id):
    if request.method != 'GET':
        raise Http404()

    try:
        id = int(id)
    except ValueError:
        raise Http404()
    exp = models.Expense.objects.get(id=id)
    #serialized = serializers.serialize('json',exp,fields=['expense_date','owner','description','reimbursement','verification'])
    #print(serialized)
    return JsonResponse({'expense':exp},status=200,safe=False)

def expenses(request):
    if request.method != 'GET':
        raise Http404()
    return JsonResponse({'expenses': models.Expense.objects.all()})


def _expense2dict(exp):
    return {
        'expense_date':exp.expense_date,
        'owner':exp.owner.user.username.__str__(),
        'description':exp.description.__str__(),
        'reimbursement':exp.reimbursement,
        'verification':exp.verification.__str__(),
        'parts': models.ExpensePart.objects.get(expense=exp.id).objectRepresentation()
    }
