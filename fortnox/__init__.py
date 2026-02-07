from functools import wraps

from django.conf import settings
from django.shortcuts import redirect

from .api_client import FortnoxAPIClient, RefreshTokenGrant
from .api_client.exceptions import FortnoxAPIError


class FortnoxMiddleware:
    """This middleware forwards a Fortnox API client and access token, if available, to views"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.client = FortnoxAPIClient(client_id=settings.FORTNOX_CLIENT_ID,
                                       client_secret=settings.FORTNOX_CLIENT_SECRET, scope=settings.FORTNOX_SCOPE)

    def __call__(self, request):
        request.fortnox_client = self.client
        request.fortnox_access_token = retrieve_or_refresh_token(self.client, request.user)
        return self.get_response(request)


# TODO: Check using expires_at instead
def retrieve_or_refresh_token(client, user):
    """Returns a valid access token for the user, if possible. Otherwise None"""
    # Lazy imports to prevent issues when loading apps
    from .models import APITokens

    if user.is_anonymous:
        return None

    try:
        tokens = APITokens.objects.get(user=user)
    except APITokens.DoesNotExist:
        return None

    try:
        client.retrieve_current_user(tokens.access_token)
        return tokens.access_token
    except FortnoxAPIError:
        # Try refreshing token
        grant = RefreshTokenGrant(code=tokens.refresh_token)
        try:
            response = client.retrieve_access_token(grant)
            APITokens.objects.update_or_create(user=user, defaults={'access_token': response.access_token,
                                                                    'refresh_token': response.refresh_token, })
            return response.access_token
        except FortnoxAPIError:
            return None


def require_fortnox_auth(view):
    """Requires the user to have a valid access or refresh token"""

    @wraps(view)
    def wrap(request, *args, **kwargs):
        token = retrieve_or_refresh_token(request.fortnox_client, request.user)
        if token is None:
            return redirect(settings.FORTNOX_AUTH_REDIRECT)
        else:
            return view(request, *args, **kwargs)

    return wrap
