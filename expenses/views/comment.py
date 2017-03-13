from django.http import HttpResponse


def comment_by_id(request,id):
    if request.method == 'PUT':
        return HttpResponse(status=501, content="Feature has not been implemented yet :(")
        # TODO: Should update the comment with the specified id
    else:
        return HttpResponse(status=501, content= request.method  + " is not a valid method to access resource!")


def comment_by_expense(request,id):
    if request.method == 'GET':
        return HttpResponse(status=501, content="Feature has not been implemented yet :(")
        # TODO: Implement, should get all comments related to expense with specified id
    else:
        return HttpResponse(status=501, content= request.method  + " is not a valid method to access resource!")


def comment(request):
    if request.method == 'PUT':
        return HttpResponse(status=501, content="Feature has not been implemented yet :(")
        # TODO: Implement, should create a comment
    else:
        return HttpResponse(status=501, content= request.method  + " is not a valid method to access resource!")

