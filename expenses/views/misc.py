from django.contrib import auth
from django.http import Http404, JsonResponse
from django.http import HttpResponse
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
        return HttpResponseRedirect(redirect_to=request.build_absolute_uri("/"))
    return JsonResponse({'status': 'failed'})


def logout(request):
    if request.method != 'GET':
        raise Http404()
    auth.logout(request)
    return HttpResponse("You are now logged out!")
