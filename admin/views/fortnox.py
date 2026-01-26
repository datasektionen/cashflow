from datetime import datetime, timedelta
import json

from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_GET
from django.urls import reverse
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseBadRequest, JsonResponse 
from django.db import connection

from fortnox.api import FortnoxAPIClient
import fortnox.models as fortnox

client = FortnoxAPIClient(
    client_id=settings.FORTNOX_CLIENT_ID,
    client_secret=settings.FORTNOX_CLIENT_SECRET,
    scope="bookkeeping%20companyinformation%20settings%20customer%20profile",
    state=settings.FORTNOX_STATE,
)

@require_GET
@login_required
@user_passes_test(lambda u: u.profile.may_view_account())
def get_auth_code(request):
    """Retrieves an auth code from Fortnox.

    When this view is triggered, the user will be redirected to a Fortnox
    login page. Upon successful authentication, the user will be redirected
    to a success page.
    """
    redirect_uri = request.build_absolute_uri(reverse('fortnox-auth-complete'))
    print(f"{redirect_uri=}")
    return HttpResponseRedirect(client.get_auth_code_url(redirect_uri))


@login_required
@user_passes_test(lambda u: u.profile.may_firmatecknare())
def auth_complete(request):
    auth_code = client.get_value_from_callback_url(request.get_full_path())
    get_tokens = client.get_access_token(auth_code)
    access_token = get_tokens['access_token']
    refresh_token = get_tokens['refresh_token']
    expires_in = get_tokens['expires_in']
    token_parts = fortnox.AuthToken.objects.all().delete()
    token_parts = fortnox.AuthToken(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=datetime.now() + timedelta(0, expires_in)
    )   
    token_parts.save()

    return render(request, 'admin/fortnox/overview.html', {
        'access_token': json.dumps(access_token, indent=4),
        'refresh_token': refresh_token,
        'expires_in': expires_in
    })


@login_required
@user_passes_test(lambda u: u.profile.may_firmatecknare())
def fortnox_auth_complete(request):
    auth_code = client.get_value_from_callback_url(request.get_full_path())
    get_tokens = client.get_access_token(auth_code)
    access_token = get_tokens['access_token']
    refresh_token = get_tokens['refresh_token']
    expires_in = get_tokens['expires_in']
    token_parts = fortnox.AuthToken.objects.all().delete()
    token_parts = fortnox.AuthToken(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=datetime.now() + timedelta(0, expires_in)
    )   
    token_parts.save()

    return render(request, 'admin/fortnox/overview.html', {
        'access_token': json.dumps(access_token, indent=4),
        'refresh_token': refresh_token,
        'expires_in': expires_in
    })


# TODO: Fix, possibly broken from python/django update
# @login_required
# def fortnox_auth_refresh(request):
#     token = fortnox.AuthToken.objects.all().first()
#     new_token = client.get_access_token_from_refresh_token(token.refresh_token)
#     token = fortnox.AuthToken.objects.all().delete()
#     token = fortnox.AuthToken(
#         access_token=new_token['access_token'],
#         refresh_token=new_token['refresh_token'],
#         expires_at=datetime.now() + timedelta(0, new_token['expires_in'])
#     )
#     token.save()


#@require_GET
@login_required
@user_passes_test(lambda u: u.profile.may_firmatecknare())
def fortnox_auth_test(request):
    token = fortnox.AuthToken.objects.all().first()
    if token is None:
        return HttpResponseBadRequest("No token found")
    company_info = client.get_company_info(token.access_token)
    # If company_info returns {'message': 'unauthorized'} then the token is invalid
    accounts = client.get_accounts(token.access_token, 13)
    accountchart = client.get_api_request(token.access_token, 'accountcharts')
    voucher_series = client.get_voucher_series(token.access_token)
    cost_centers = client.get_cost_centers(token.access_token)
    expenses = client.get_api_request(token.access_token, 'expenses')
    labels = client.get_api_request(token.access_token, 'labels')
    predefined_accounts = client.get_api_request(token.access_token, 'predefinedaccounts')
    return render(request, 'admin/auth/test.html', {
        'company_info': company_info,
        'accounts': accounts,
        'accountchart': accountchart,
        'voucher_series': voucher_series,
        'cost_centers': cost_centers,
        'expenses': expenses,
        'labels': labels,
        'predefined_accounts': predefined_accounts
    })

@login_required
@user_passes_test(lambda u: u.profile.may_firmatecknare())
def fortnox_import_accounts_to_db(request):
    token = fortnox.AuthToken.objects.all().first()
    if token is None:
        return HttpResponseBadRequest("No token found")
    # Get all accounts from Fortnox thru all pages and save them to the database
    page_number = 0

    fortnox.Account.objects.all().delete()
    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE expenses_fortnoxaccounts RESTART IDENTITY;")

    while True:
        accounts = client.get_accounts(token.access_token, page_number)
        if page_number > accounts.get('MetaInformation', {}).get('@TotalPages', 0):
            break
        for account in accounts['Accounts']:
            account_db = fortnox.Account(
                URL="None" if account.get('@url') is None else account.get('@url'),
                Active="None" if account.get('Active') is None else account.get('Active'),
                BalanceBroughtForward=0 if account.get('BalanceBroughtForward') is None else account.get('BalanceBroughtForward'),
                CostCenter="None" if account.get('CostCenter') is None else account.get('CostCenter'),
                CostCenterSettings="None" if account.get('CostCenterSettings') is None else account.get('CostCenterSettings'),
                Description="None" if account.get('Description') is None else account.get('Description'),
                Number=account.get('Number'),
                Project="None" if account.get('Project') is None else account.get('Project'),
                ProjectSettings="None" if account.get('ProjectSettings') is None else account.get('ProjectSettings'),
                SRU=0 if account.get('SRU') is None else account.get('SRU'),
                VATCode="None" if account.get('VATCode') is None else account.get('VATCode'),
                Year=0 if account.get('Year') is None else account.get('Year')
            )
            account_db.save()
        page_number += 1
    return HttpResponseRedirect(reverse('admin-auth-test'))

@require_GET
@login_required
@require_GET
@login_required
@user_passes_test(lambda u: u.profile.may_firmatecknare())
def fortnox_auth_search(request):
    token = fortnox.AuthToken.objects.first()
    if token is None:
        return JsonResponse({'error': 'No token found'})

    search_query = request.GET.get('search')

    search_results = fortnox.Account.objects.filter(
        Description__icontains=search_query
    ) | fortnox.Account.objects.filter(Number__icontains=search_query)

    results_list = list(search_results.values('Number', 'Description'))
    return JsonResponse({'accounts': results_list})


