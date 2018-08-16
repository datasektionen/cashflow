from django.contrib import auth
from django.http import HttpResponseRedirect, Http404


def login(request):
    """
    Login route, redirects to login2 login URL.
    """
    if not request.user.is_authenticated:
        return HttpResponseRedirect(
            'https://login2.datasektionen.se/login?callback=' +
            request.scheme + '://' + request.get_host() + '/login/')
    else:
        return HttpResponseRedirect("/")


def login_with_token(request, token):
    """
    Handles a login2 redirect and authenticates user.
    """
    if request.method != 'GET':
        raise Http404()
    user = auth.authenticate(token=token)
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
