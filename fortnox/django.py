"""
This module defines Django-specific functionality tied to the Fortnox integration.
"""
from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from structlog import get_logger

from fortnox import FortnoxAPIClient, RefreshTokenGrant, FortnoxAuthenticationError, exceptions

logger = get_logger(__name__)


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
        from .models import ServiceAccount

        allowed = (not request.user.is_anonymous and (self.auth_callback is None or self.auth_callback(request.user)))

        if allowed:
            try:
                client = FortnoxAPIClient(client_id=settings.FORTNOX_CLIENT_ID,
                                          client_secret=settings.FORTNOX_CLIENT_SECRET, scope=settings.FORTNOX_SCOPE, )
                client.token_provider = lambda: retrieve_or_refresh_token(client)
                request.fortnox_service = client
            except ServiceAccount.DoesNotExist:
                request.fortnox_service = None
        else:
            request.fortnox_service = None

        return self.get_response(request)


def require_fortnox_permission(view):
    """Requires the user to pass the FORTNOX_ALLOW_AUTHENTICATION_CALLBACK check.

    Prevents anyone but the Fortnox admin (Kassör) to authenticate the service account.
    """

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


def require_fortnox_service(view):
    """Requires a valid service account token to be present."""

    @wraps(view)
    def wrap(request: FortnoxRequest, *args, **kwargs):
        token = retrieve_or_refresh_token(request.fortnox)
        if token is None:
            error_dict = exceptions.FortnoxServiceNotAvailableError().to_dict()
            logger.error("fortnox access token not available")
            return JsonResponse(error_dict)
        return view(request, *args, **kwargs)

    return wrap


def retrieve_or_refresh_token(client):
    # Lazy imports to prevent issues when loading apps
    from .models import ServiceAccount

    with transaction.atomic():
        try:
            service_account = ServiceAccount.objects.select_for_update().get()
        except ServiceAccount.DoesNotExist:
            return None

        if service_account.expires_at > timezone.now():
            return service_account.access_token

        else:

            logger.debug(f"Attempting to refresh access token for Fortnox")
            grant = RefreshTokenGrant(code=service_account.refresh_token)
            try:
                response = client.retrieve_access_token(grant)

                service_account.access_token = response.access_token
                service_account.refresh_token = response.refresh_token
                service_account.expires_at = timezone.now() + timedelta(seconds=response.expires_in)
                service_account.save(update_fields=["access_token", "refresh_token", "expires_at"])

                logger.info(f"refreshed access token for Fortnox", new_token_id=service_account.pk,
                            new_token_expires_at=service_account.expires_at, )
                return response.access_token
            except FortnoxAuthenticationError:
                # Most likely both tokens are expired
                # Better to "de-authenticate" user completely
                existing = ServiceAccount.objects.get()
                logger.error("failed to refresh access token for Fortnox, invalidating tokens", token_id=existing.pk,
                             access_token_expires_at=existing.expires_at, )
                ServiceAccount.objects.get().delete()
                return None
