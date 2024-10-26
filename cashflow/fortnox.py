import base64
import json
from urllib.parse import parse_qs, urlparse
from urllib.request import HTTPBasicAuthHandler
import requests
from django.conf import settings

#scope = "bookkeeping%20companyinformation%20settings%20costcenter%price%20customer%20profile"
scope = "bookkeeping%20companyinformation%20settings%20customer%20profile"

redirect_uri = "http://localhost:8000/admin/auth/complete"
access_type = "offline"
fortnox_url = "https://apps.fortnox.se/oauth-v1/"
api_url = "https://api.fortnox.se/3/"

class FortnoxAPI(object):
    """
    A class to interact with Fortnox API.
    """
    def get_auth_code():
        return f"https://apps.fortnox.se/oauth-v1/auth?client_id={settings.FORTNOX_CLIENT_ID}&redirect_uri={redirect_uri}&scope={scope}&state={settings.FORTNOX_STATE}&access_type={access_type}&response_type=code&account_type=service"
    
    def get_value_from_callback_url(url):
        parsed_url = urlparse(url)
        captured_value = parse_qs(parsed_url.query)['code'][0]
        return captured_value
    
    def get_access_token(auth_code):
        token_url = fortnox_url + "token"
        credentials = f"{settings.FORTNOX_CLIENT_ID}:{settings.FORTNOX_CLIENT_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
        }
        body = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': redirect_uri
        }
        response = requests.post(token_url, headers=headers, data=body)
        return response.json()
    
    def get_access_token_from_refresh_token(refresh_token):
        token_url = fortnox_url + "token"
        credentials = f"{settings.FORTNOX_CLIENT_ID}:{settings.FORTNOX_CLIENT_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
        }
    
        body = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        response = requests.post(token_url, headers=headers, data=body)
        return response.json
    
    def get_api_request(access_token, endpoint):
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(api_url+endpoint, headers=headers)
        return response.json()
    
    def get_company_info(access_token):
        company_info_url = 'https://api.fortnox.se/3/companyinformation'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(company_info_url, headers=headers)
        return response.json()
    
    def get_accounts(access_token):
        account_url = 'https://api.fortnox.se/3/accounts?page=0'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(account_url, headers=headers)
        return response.json()
    
    def get_voucher_series(access_token):
        voucher_series_url = 'https://api.fortnox.se/3/voucherseries'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(voucher_series_url, headers=headers)
        return response.json()
    
    # https://api.fortnox.se/3/costcenters
    def get_cost_centers(access_token):
        cost_centers_url = 'https://api.fortnox.se/3/costcenters'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(cost_centers_url, headers=headers)

    # https://api.fortnox.se/3/expenses
