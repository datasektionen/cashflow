from django.http import HttpResponse


def bookkeeping(request):
    if request.method == 'GET':
        return HttpResponse(status=501, content="Feature has not been implemented yet :(")
        # TODO: Implement, should return all paid non book-kept expenses
    elif request.method == 'PUT':
        return HttpResponse(status=501, content="Feature has not been implemented yet :(")
        # TODO: Implement, should assign a journal number to a expense
    else:
        return HttpResponse(status=501, content=request.method + " is not a valid method to access resource!")
