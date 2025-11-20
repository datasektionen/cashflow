from django.contrib import auth
from django.http import HttpResponseRedirect, Http404

from cashflow import settings, dauth


def login(request):
    """
    Login route, redirects to the login system.
    """
    if "code" in request.GET:
        return login_with_token(request)
    elif not request.user.is_authenticated:
        return dauth.client.authorize_redirect(request, settings.REDIRECT_URL)
    else:
        return HttpResponseRedirect("/")


def login_with_token(request):
    """
    Handles a login redirect and authenticates user.
    """
    if request.method != 'GET':
        raise Http404()
    user = auth.authenticate(request)
    if user is not None:
        auth.login(request, user)
        return HttpResponseRedirect(redirect_to=request.build_absolute_uri("/"))
    return HttpResponseRedirect("/")  # fail silently


def logout(request):
    """
    Logs out user.
    """
    auth.logout(request)
    return HttpResponseRedirect("/")
