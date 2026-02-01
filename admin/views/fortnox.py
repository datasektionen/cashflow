import secrets

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_GET

from fortnox.api_client import FortnoxAPIClient, AuthCodeGrant, RefreshTokenGrant
from fortnox.api_client.exceptions import FortnoxAPIError
from fortnox.models import APITokens


class CSRFValidationError(PermissionError):
    pass


client = FortnoxAPIClient(client_id=settings.FORTNOX_CLIENT_ID, client_secret=settings.FORTNOX_CLIENT_SECRET,
                          scope=['bookkeeping', 'companyinformation', 'settings', 'customer', 'profile'])


# TODO: Check using expires_at instead
def check_or_update_token(user):
    """Returns a valid access token for the user, if possible. Otherwise None"""
    try:
        tokens = APITokens.objects.get(user=user)
    except APITokens.DoesNotExist:
        return None

    try:
        client.get_user_info(tokens.access_token)
        return tokens.access_token
    except FortnoxAPIError:
        # Try refreshing token
        grant = RefreshTokenGrant(code=tokens.refresh_token)
        try:
            response = client.get_access_token(grant)
            APITokens.objects.update_or_create(user=user, defaults={'access_token': response.access_token,
                                                                    'refresh_token': response.refresh_token, })
            return response.access_token
        except FortnoxAPIError:
            return None


@require_GET
@login_required
def get_auth_code(request):
    """Retrieves an auth code from Fortnox.

    When this view is triggered, the user will be redirected to a Fortnox
    login page. Upon successful authentication, the user will be redirected
    to a success page.
    """

    # Generate a token for CSRF protection
    csrf_token = secrets.token_urlsafe(32)
    request.session['fortnox_csrf_token'] = csrf_token

    redirect_uri = request.build_absolute_uri(reverse('fortnox-auth-complete'))
    return HttpResponseRedirect(client.get_auth_code_url(redirect_uri, csrf_token))


@login_required
@user_passes_test(lambda u: u.profile.may_firmatecknare())
def auth_complete(request):
    redirect_uri = request.build_absolute_uri(reverse('fortnox-auth-complete'))

    # Validate CSRF token integrity
    client_token = request.session.get('fortnox_csrf_token')
    response_token = request.GET.get('state')
    match client_token, response_token:
        case _, None:
            raise CSRFValidationError('CSRF token missing from API response')
        case None, _:
            raise CSRFValidationError('CSRF token missing from session storage')
        case a, b if a != b:
            raise CSRFValidationError('Mismatched CSRF tokens')
        case a, b if a == b:
            # OK
            request.session.delete('fortnox_csrf_token')

    # Get auth code from URL parameters
    match request.GET.get('code'), request.GET.get('error'):
        case None, e:
            print(e)
            # TODO: Error handling
            return redirect(reverse('admin-index'))
        case auth_code, _:
            # TODO: Error handling
            response = client.get_access_token(AuthCodeGrant(code=auth_code, redirect_uri=redirect_uri))
            APITokens.objects.update_or_create(user=request.user, defaults={'access_token': response.access_token,
                                                                            'refresh_token': response.refresh_token, })

    return redirect(reverse('fortnox-overview'))


@login_required
@user_passes_test(lambda u: u.profile.may_firmatecknare())
def overview(request):
    access_token = check_or_update_token(request.user)
    if access_token is not None:
        user_info = client.get_user_info(access_token)
        fortnox_user = user_info.model_dump()
    else:
        fortnox_user = None

    return render(request, 'admin/fortnox/overview.html', {'fortnox_user':fortnox_user})
