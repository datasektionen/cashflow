import secrets

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_GET

from fortnox import require_fortnox_auth
from fortnox.api_client import AuthCodeGrant
from fortnox.models import APITokens


class CSRFValidationError(PermissionError):
    pass


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
    return HttpResponseRedirect(request.fortnox_client.build_auth_code_url(redirect_uri, csrf_token))


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
            response = request.fortnox_client.retrieve_access_token(
                AuthCodeGrant(code=auth_code, redirect_uri=redirect_uri))
            APITokens.objects.update_or_create(user=request.user, defaults={'access_token': response.access_token,
                                                                            'refresh_token': response.refresh_token, })

    return redirect(reverse('fortnox-overview'))


@login_required
@user_passes_test(lambda u: u.profile.may_firmatecknare())
@require_fortnox_auth
def overview(request):
    user_info = request.fortnox_client.retrieve_current_user(request.fortnox_access_token)
    fortnox_user = user_info.model_dump()

    accounts = request.fortnox_client.list_accounts(request.fortnox_access_token)
    accounts = [account for account in accounts if account.Active]
    accounts = [a.model_dump() for a in accounts]

    return render(request, 'admin/fortnox/overview.html', {'fortnox_user': fortnox_user, 'accounts': accounts})
