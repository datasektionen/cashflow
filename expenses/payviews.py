from django.http import HttpResponse


def payment(request,id):
    if request.method == 'GET':
        return HttpResponse(status=501, content="Feature has not been implemented yet :(")
        # TODO: should retrieve the payment with the specified id
    elif request.method == 'PUT':
        return HttpResponse(status=501, content="Feature has not been implemented yet :(")
    else:
        return HttpResponse(status=501, content= request.method  + " is not a valid method to access resource!")


def pay(request):
    if request.method == 'GET':
        return HttpResponse(status=501, content="Feature has not been implemented yet :(")
        # TODO: Implement, should return all non-paid fully attested expenses
    elif request.method == 'PUT':
        return HttpResponse(status=501, content="Feature has not been implemented yet :(")
        # TODO: Implement, should create a payment and update expenses with payment
    else:
        return HttpResponse(status=501, content= request.method  + " is not a valid method to access resource!")

