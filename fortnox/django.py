"""
This module defines Django-specific functionality tied to the Fortnox integration.
"""
import logging
from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import redirect
from django.utils import timezone

from fortnox import FortnoxAPIClient, RefreshTokenGrant, FortnoxAuthenticationError

logger = logging.getLogger(__name__)


class FortnoxRequest(HttpRequest):
    """This subclass allows for proper type hinting in views.

    Instead of writing e.g. `def my_view(request: HttpRequest)` you can write
    `def my_view(request: FortnoxRequest)`, and you will get hints for the api client.
    """
    fortnox: FortnoxAPIClient


class FortnoxMiddleware:
    """This middleware forwards a Fortnox API client and access token, if available, to views"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_anonymous:
            client = FortnoxAPIClient(client_id=settings.FORTNOX_CLIENT_ID,
                                      client_secret=settings.FORTNOX_CLIENT_SECRET, scope=settings.FORTNOX_SCOPE)
            # Evil closure
            client.token_provider = lambda: retrieve_or_refresh_token(client, request.user)
            request.fortnox = client
        else:
            request.fortnox = None

        return self.get_response(request)


def retrieve_or_refresh_token(client, user):
    """Returns a valid access token for the user, if possible. Otherwise None"""
    # Lazy imports to prevent issues when loading apps
    from .models import APIUser

    if user.is_anonymous:
        return None

    try:
        api_user = user.fortnox
    except APIUser.DoesNotExist:
        return None

    if api_user.expires_at > timezone.now():
        logger.debug(f"{user} has an active access token")
        return api_user.access_token
    else:
        logger.debug(f"Attempting to refresh access token for {user}")
        grant = RefreshTokenGrant(code=api_user.refresh_token)
        try:
            response = client.retrieve_access_token(grant)
            APIUser.objects.update_or_create(user=user, defaults={"access_token": response.access_token,
                                                                  "refresh_token": response.refresh_token,
                                                                  "expires_at": timezone.now() + timedelta(
                                                                      seconds=response.expires_in)})
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
    def wrap(request: FortnoxRequest, *args, **kwargs):
        token = retrieve_or_refresh_token(request.fortnox, request.user)
        if token is None:
            return redirect(settings.FORTNOX_AUTH_REDIRECT)
        else:
            return view(request, *args, **kwargs)

    return wrap
