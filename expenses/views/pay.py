from django.http import HttpResponse, JsonResponse
from expenses.models import Expense, Payment


def payment(request,id):
    if request.method == 'GET':
        return HttpResponse(status=501, content="Feature has not been implemented yet :(")
        # TODO: should retrieve the payment with the specified id
    elif request.method == 'PUT':
        return HttpResponse(status=501, content="Feature has not been implemented yet :(")
        # TODO: should update the payment with the specified id
    else:
        return HttpResponse(status=501, content= request.method  + " is not a valid method to access resource!")


def pay(request):
    if request.method == 'GET':
        ready_to_pay_expenses = []

        to_be_paid_expenses = Expense.objects.filter(reimbursement__isnull=True)

        for expense in to_be_paid_expenses:
            if len(expense.expensepart_set.filter(attested_by__isnull=True)) == 0:  # All parts attested
                ready_to_pay_expenses.append(expense.to_dict())

        return JsonResponse({'expenses':ready_to_pay_expenses})
    elif request.method == 'PUT':
        return HttpResponse(status=501, content="Feature has not been implemented yet :(")
        # TODO: Implement, should create a payment and update expenses with payment
    else:
        return HttpResponse(status=501, content= request.method  + " is not a valid method to access resource!")

