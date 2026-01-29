import requests
from urllib.parse import urlparse, parse_qs
import base64


class FortnoxAPIClient:
    """
    A class to interact with Fortnox API.
    """
    API_URL = "https://api.fortnox.se/3/"
    FORTNOX_URL = "https://apps.fortnox.se/oauth-v1"

    def __init__(self, client_id, client_secret, scope, state, access_type='offline'):
        # It's possible some of these should be moved inside certain methods
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.state = state
        self.access_type = access_type
        self.redirect_uri = None


    def get_auth_code_url(self, redirect_uri):

        # According to the API documentation, you always
        # have to use the same redirect uri that you used
        # when getting the auth code, so we save it
        # https://www.fortnox.se/developer/authorization/get-access-token
        self.redirect_uri = redirect_uri

        return f"{self.FORTNOX_URL}/auth?client_id={self.client_id}&redirect_uri={redirect_uri}&scope={self.scope}&state={self.state}&access_type={self.access_type}&response_type=code&account_type=service"

    def get_access_token(self, auth_code):
        token_url = f"{self.FORTNOX_URL}/token"
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
        }
        body = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': self.redirect_uri

        }
        response = requests.post(token_url, headers=headers, data=body)
        return response.json()
    
    def get_access_token_from_refresh_token(self, refresh_token):
        token_url = f"{self.FORTNOX_URL}/token"
        credentials = f"{self.client_id}:{self.client_secret}"
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
    
    @classmethod
    def get_api_request(cls, access_token, endpoint):
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(f"{cls.API_URL}/{endpoint}", headers=headers)
        return response.json()
    
    @staticmethod
    def get_company_info(access_token):
        company_info_url = 'https://api.fortnox.se/3/companyinformation'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(company_info_url, headers=headers)
        return response.json()
    
    @staticmethod
    def get_accounts(access_token, page):
        account_url = 'https://api.fortnox.se/3/accounts?page=' + str(page)
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(account_url, headers=headers)
        return response.json()
    
    @staticmethod
    def get_voucher_series(access_token):
        voucher_series_url = 'https://api.fortnox.se/3/voucherseries'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(voucher_series_url, headers=headers)
        return response.json()
    
    # https://api.fortnox.se/3/costcenters
    @staticmethod
    def get_cost_centers(access_token):
        cost_centers_url = 'https://api.fortnox.se/3/costcenters'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(cost_centers_url, headers=headers)

