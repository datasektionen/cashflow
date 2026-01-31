import secrets

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import connection
from django.http import HttpResponseRedirect, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_GET

from fortnox.api_client import FortnoxAPIClient, AuthCodeGrant, ExternalAPIError, RefreshTokenGrant
from fortnox.models import APITokens, Account


class CSRFValidationError(PermissionError):
    pass


client = FortnoxAPIClient(client_id=settings.FORTNOX_CLIENT_ID, client_secret=settings.FORTNOX_CLIENT_SECRET,
                          scope="bookkeeping%20companyinformation%20settings%20customer%20profile")


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
    except ExternalAPIError:
        # Try refreshing token
        grant = RefreshTokenGrant(code=tokens.refresh_token)
        try:
            response = client.get_access_token(grant)
            APITokens.objects.update_or_create(user=user, defaults={'access_token': response.access_token,
                                                                    'refresh_token': response.refresh_token, })
            return response.access_token
        except ExternalAPIError:
            return None


@require_GET
@login_required
# @user_passes_test(lambda u: u.profile.may_view_account())
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
        case None, _:
            # TODO: Error handling
            return redirect(reverse('fortnox-overview'))
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
    if access_token is None:
        return redirect(reverse('fortnox-auth-get'))

    user_info = client.get_user_info(access_token)

    return render(request, 'admin/fortnox/overview.html', {'fortnox_user': user_info.model_dump()})


@login_required
@user_passes_test(lambda u: u.profile.may_firmatecknare())
def fortnox_import_accounts_to_db(request):
    token = APITokens.objects.all().first()
    if token is None:
        return HttpResponseBadRequest("No token found")
    # Get all accounts from Fortnox thru all pages and save them to the database
    page_number = 0

    Account.objects.all().delete()
    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE expenses_fortnoxaccounts RESTART IDENTITY;")

    while True:
        accounts = client.get_accounts(token.access_token, page_number)
        if page_number > accounts.get('MetaInformation', {}).get('@TotalPages', 0):
            break
        for account in accounts['Accounts']:
            account_db = Account(URL="None" if account.get('@url') is None else account.get('@url'),
                                 Active="None" if account.get('Active') is None else account.get('Active'),
                                 BalanceBroughtForward=0 if account.get(
                                     'BalanceBroughtForward') is None else account.get('BalanceBroughtForward'),
                                 CostCenter="None" if account.get('CostCenter') is None else account.get('CostCenter'),
                                 CostCenterSettings="None" if account.get(
                                     'CostCenterSettings') is None else account.get('CostCenterSettings'),
                                 Description="None" if account.get('Description') is None else account.get(
                                     'Description'), Number=account.get('Number'),
                                 Project="None" if account.get('Project') is None else account.get('Project'),
                                 ProjectSettings="None" if account.get('ProjectSettings') is None else account.get(
                                     'ProjectSettings'), SRU=0 if account.get('SRU') is None else account.get('SRU'),
                                 VATCode="None" if account.get('VATCode') is None else account.get('VATCode'),
                                 Year=0 if account.get('Year') is None else account.get('Year'))
            account_db.save()
        page_number += 1
    return HttpResponseRedirect(reverse('admin-auth-test'))


@require_GET
@login_required
@require_GET
@login_required
@user_passes_test(lambda u: u.profile.may_firmatecknare())
def fortnox_auth_search(request):
    token = APITokens.objects.first()
    if token is None:
        return JsonResponse({'error': 'No token found'})

    search_query = request.GET.get('search')

    search_results = Account.objects.filter(Description__icontains=search_query) | Account.objects.filter(
        Number__icontains=search_query)

    results_list = list(search_results.values('Number', 'Description'))
    return JsonResponse({'accounts': results_list})
