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
from django.db import transaction

from fortnox import FortnoxAPIClient, RefreshTokenGrant, FortnoxAuthenticationError

logger = logging.getLogger(__name__)


class FortnoxRequest(HttpRequest):
    """This subclass allows for proper type hinting in views.

    Instead of writing e.g. `def my_view(request: HttpRequest)` you can write
    `def my_view(request: FortnoxRequest)`, and you will get hints for the api client.
    """
    fortnox: FortnoxAPIClient
    fortnox_service: FortnoxAPIClient | None


class FortnoxMiddleware:
    """This middleware forwards a Fortnox API client and access token, if available, to views"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_anonymous:
            client = FortnoxAPIClient(client_id=settings.FORTNOX_CLIENT_ID,
                                      client_secret=settings.FORTNOX_CLIENT_SECRET, scope=settings.FORTNOX_SCOPE)
            # Evil closure
            client.token_provider = lambda: retrieve_or_refresh_token(client)
            request.fortnox = client
        else:
            request.fortnox = None

        return self.get_response(request)


class FortnoxServiceMiddleware:
    """Attaches a Fortnox service account client to request.fortnox_service.

    auth_callback(user) -> bool determines whether the requesting user may use
    the service account. Falls back to settings.FORTNOX_SERVICE_AUTH (a dotted
    import path) if no callback is passed. If neither is set, the client is
    attached for all authenticated users.
    """

    def __init__(self, get_response, auth_callback=None):
        self.get_response = get_response
        if auth_callback is not None:
            self.auth_callback = auth_callback
        else:
            path = getattr(settings, 'FORTNOX_SERVICE_AUTH', None)
            if path:
                from django.utils.module_loading import import_string
                self.auth_callback = import_string(path)
            else:
                self.auth_callback = None

    def __call__(self, request):
        from .models import APIUser

        allowed = (
            not request.user.is_anonymous
            and (self.auth_callback is None or self.auth_callback(request.user))
        )

        if allowed:
            try:
                api_user = APIUser.objects.get()
                client = FortnoxAPIClient(
                    client_id=settings.FORTNOX_CLIENT_ID,
                    client_secret=settings.FORTNOX_CLIENT_SECRET,
                    scope=settings.FORTNOX_SCOPE,
                )
                client.token_provider = lambda: retrieve_or_refresh_token(client)
                request.fortnox_service = client
            except APIUser.DoesNotExist:
                request.fortnox_service = None
        else:
            request.fortnox_service = None

        return self.get_response(request)



def require_fortnox_permission(view):
    """Requires the user to pass the FORTNOX_ALLOW_AUTHENTICATION_CALLBACK check."""

    @wraps(view)
    def wrap(request, *args, **kwargs):
        path = getattr(settings, 'FORTNOX_ALLOW_AUTHENTICATION_CALLBACK', None)
        if path:
            from django.utils.module_loading import import_string
            callback = import_string(path)
            if not callback(request.user):
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrap


def require_fortnox_auth(view):
    """Requires a valid service account token to be present."""

    @wraps(view)
    def wrap(request: FortnoxRequest, *args, **kwargs):
        token = retrieve_or_refresh_token(request.fortnox)
        if token is None:
            return redirect(settings.FORTNOX_AUTH_REDIRECT)
        return view(request, *args, **kwargs)

    return wrap


def retrieve_or_refresh_token(client):
    # Lazy imports to prevent issues when loading apps
    from .models import APIUser

    with transaction.atomic():
        try:
            api_user = APIUser.objects.select_for_update().get()
        except APIUser.DoesNotExist:
            return None

        if api_user.expires_at > timezone.now():
            return api_user.access_token

        else:

            logger.debug(f"Attempting to refresh access token for Fortnox")
            grant = RefreshTokenGrant(code=api_user.refresh_token)
            try:
                response = client.retrieve_access_token(grant)

                api_user.access_token = response.access_token
                api_user.refresh_token = response.refresh_token
                api_user.expires_at = timezone.now() + timedelta(seconds=response.expires_in)
                api_user.save(update_fields=["access_token", "refresh_token", "expires_at"])

                logger.debug(f"Successfully refreshed access token for Fortnox")
                return response.access_token
            except FortnoxAuthenticationError as e:
                logger.debug(f"Failed to refresh access token for Fortnox: {e}")
                # Most likely both tokens are expired
                # Better to "de-authenticate" user completely
                logger.error(f"Fortnox tokens are expired or otherwise invalid -- deleting saved tokens")
                APIUser.objects.get().delete()
                return None
