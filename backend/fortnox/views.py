import secrets
from datetime import timedelta

import structlog
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from fortnox.api_client import AuthCodeGrant
from fortnox.django import FortnoxRequest, require_fortnox_permission
from fortnox.models import ServiceAccount

logger = structlog.get_logger(__name__)


class CSRFValidationError(PermissionError):
    pass


def _frontend_redirect(status: str) -> HttpResponseRedirect:
    """Redirect the browser back into the SvelteKit Fortnox page."""
    return redirect(f"{settings.FRONTEND_URL}/admin/fortnox?fortnox={status}")


@require_GET
@login_required
@require_fortnox_permission
def get_auth_code(request):
    """Retrieves an auth code from Fortnox.

    When this view is triggered, the user will be redirected to a Fortnox
    login page. Upon successful authentication, the user will be redirected
    back into the frontend.
    """

    # Generate a token for CSRF protection
    csrf_token = secrets.token_urlsafe(32)
    request.session["fortnox_csrf_token"] = csrf_token

    logger.info("started authentication flow for Fortnox service account")

    redirect_uri = request.build_absolute_uri(reverse("fortnox-auth-complete"))
    return HttpResponseRedirect(
        request.fortnox.build_auth_code_url(redirect_uri, csrf_token)
    )


@login_required
@require_fortnox_permission
def auth_complete(request: FortnoxRequest):
    assert isinstance(request.user, User)
    redirect_uri = request.build_absolute_uri(reverse("fortnox-auth-complete"))

    # Validate CSRF token integrity
    client_token = request.session.get("fortnox_csrf_token")
    response_token = request.GET.get("state")
    match client_token, response_token:
        case _, None:
            raise CSRFValidationError("CSRF token missing from API response")
        case None, _:
            raise CSRFValidationError("CSRF token missing from session storage")
        case a, b if a != b:
            raise CSRFValidationError("Mismatched CSRF tokens")
        case a, b if a == b:
            # OK
            request.session.delete("fortnox_csrf_token")

    # Get auth code from URL parameters
    match request.GET.get("code"), request.GET.get("error"):
        case None, e:
            logger.error(
                "fortnox error when authenticating",
                error_message=e,
            )
            return _frontend_redirect("error")
        case auth_code, _:
            response = request.fortnox.retrieve_access_token(
                AuthCodeGrant(code=auth_code, redirect_uri=redirect_uri)
            )
            ServiceAccount.objects.all().delete()
            new = ServiceAccount.objects.create(
                authenticated_by=request.user,
                access_token=response.access_token,
                refresh_token=response.refresh_token,
                expires_at=timezone.now() + timedelta(seconds=response.expires_in),
            )
            logger.info(
                "fortnox successfully authenticated",
                token_id=new.pk,
                token_expires_at=new.expires_at,
            )

    return _frontend_redirect("success")
