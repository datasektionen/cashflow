from django.contrib import auth
from django.http import HttpResponseRedirect, Http404

from cashflow import settings, dauth


def login(request):
    """
    Login route, redirects to the login system.
    """
    next = request.GET.get("next", "/")
    if "code" in request.GET:
        return login_with_token(request)
    elif not request.user.is_authenticated:
        # The authlib library seems to be broken and passing the "next" parameter
        # through the state parameter does not work, so we save it in the session instead.
        request.session['login_next'] = next
        return dauth.client.authorize_redirect(request, settings.REDIRECT_URL)
    else:
        return HttpResponseRedirect(next)


def login_with_token(request):
    """
    Handles a login redirect and authenticates user.
    """
    if request.method != "GET":
        raise Http404()
    user = auth.authenticate(request)
    next = request.session.pop('login_next', '/')
    if user is not None:
        auth.login(request, user)
    return HttpResponseRedirect(next)


def logout(request):
    """
    Logs out user.
    """
    auth.logout(request)
    return HttpResponseRedirect("/")
