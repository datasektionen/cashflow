from django.contrib import auth
from django.http import Http404, JsonResponse
from django.http import HttpResponseRedirect

from expenses.models import Committee


def budget(request):
    if request.method != 'GET':
        raise Http404()
    return JsonResponse({'committees': [committee.get_overview_dict() for committee in Committee.objects.all()]})


def login(request, token):
    if request.method != 'GET':
        raise Http404()
    user = auth.authenticate(token=token)
    if user is not None:
        auth.login(request, user)
        return HttpResponseRedirect(redirect_to="http://127.0.0.1:8000/")
    return JsonResponse({'status': 'failed'})


def logout(request):
    if request.method != 'GET':
        raise Http404()
    auth.logout(request)
    return HttpResponseRedirect(redirect_to="http://127.0.0.1:8000/")
