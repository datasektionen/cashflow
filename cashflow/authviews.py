from django.contrib import auth
from django.http import HttpResponseRedirect


def login(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(
            'https://login2.datasektionen.se/login?callback=' +
            request.scheme + '://' + request.get_host() + '/api/login/')
    else:
        return HttpResponseRedirect("/")


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/")
