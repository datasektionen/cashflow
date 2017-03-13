from django.http import Http404, JsonResponse, HttpResponseForbidden
from expenses.models import Committee, Person
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from cashflow.dauth import has_permission


def budget(request):
    if request.method != 'GET':
        raise Http404()
    return JsonResponse({'committees': [committee.get_overview_dict() for committee in Committee.objects.all()]})


def user_by_username(request, username):
    if not (request.user.username == username or has_permission("pay",request.user)):
        return HttpResponseForbidden()

    if request.method != 'GET':
        raise Http404()
    try:
        user = User.objects.get(username=username)
    except ObjectDoesNotExist:
        raise Http404()
    return JsonResponse({'user': Person.objects.get(user=user).to_dict()})


def current_user(request):
    if request.method != 'GET':
        raise Http404()
    return JsonResponse({'user': Person.objects.get(user=request.user).to_dict()})