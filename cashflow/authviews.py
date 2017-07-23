from django.contrib import auth
from django.http import HttpResponseRedirect, Http404


def login(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(
            'https://login2.datasektionen.se/login?callback=' +
            request.scheme + '://' + request.get_host() + '/login/')
    else:
        return HttpResponseRedirect("/")


def login_with_token(request, token):
    if request.method != 'GET':
        raise Http404()
    user = auth.authenticate(token=token)
    if user is not None:
        auth.login(request, user)
        return HttpResponseRedirect(redirect_to=request.build_absolute_uri("/"))
    return HttpResponseRedirect("/")  # fail silently


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/")
