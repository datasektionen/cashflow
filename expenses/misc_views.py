from django.http import Http404, JsonResponse
from expenses.models import Committee, Person
from django.contrib.auth.models import User

def budget(request):
    if request.method != 'GET':
        raise Http404()
    return JsonResponse({'committees': [committee.get_overview_dict() for committee in Committee.objects.all()]})


def user_by_username(request, username):
    if request.method != 'GET':
        raise Http404()
    user = User.objects.get(username=username)
    return JsonResponse({'user': Person.objects.get(user=user).to_dict()})


def current_user(request):
    if request.method != 'GET':
        raise Http404()
    return JsonResponse({'user': Person.objects.get(user=request.user).to_dict()})