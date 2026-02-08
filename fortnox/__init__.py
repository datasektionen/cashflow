import logging
from functools import wraps

from django.conf import settings
from django.shortcuts import redirect

from .api_client import FortnoxAPIClient, RefreshTokenGrant
from .api_client.exceptions import FortnoxAPIError, FortnoxNotFound, FortnoxAuthenticationError

logger = logging.getLogger(__name__)


class FortnoxMiddleware:
    """This middleware forwards a Fortnox API client and access token, if available, to views"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.client = FortnoxAPIClient(client_id=settings.FORTNOX_CLIENT_ID,
                                       client_secret=settings.FORTNOX_CLIENT_SECRET, scope=settings.FORTNOX_SCOPE)

    def __call__(self, request):
        from .models import APIUser

        request.fortnox_client = self.client
        return self.get_response(request)


# TODO: Check using expires_at instead
def retrieve_or_refresh_token(client, user):
    """Returns a valid access token for the user, if possible. Otherwise None"""
    # Lazy imports to prevent issues when loading apps
    from .models import APIUser

    if user.is_anonymous:
        return None

    try:
        token = user.fortnox.access_token
    except APIUser.DoesNotExist:
        return None

    try:
        # Test validity
        client.retrieve_current_user(token)
        return token
    except FortnoxNotFound as e:
        logger.debug(f"Missing or invalid access token for {user}: {e}\nAttempting to refresh access token")
        # Try refreshing token
        grant = RefreshTokenGrant(code=user.fortnox.refresh_token)
        try:
            response = client.retrieve_access_token(grant)
            APIUser.objects.update_or_create(user=user, access_token=response.access_token,
                                             refresh_token=response.refresh_token)
            logger.debug(f"Successfully refreshed access token for {user}")
            return response.access_token
        except FortnoxAuthenticationError as e:
            logger.debug(f"Failed to refresh access token for {user}: {e}")
            # Most likely both tokens are expired
            # Better to "de-authenticate" user completely
            logger.info(f"Fortnox tokens for {user} are expired or otherwise invalid -- deleting saved tokens")
            APIUser.objects.get(user=user).delete()
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
