import base64
from typing import Union

import requests
from pydantic import BaseModel, TypeAdapter


class AccessTokenResponse(BaseModel):
    # https://www.fortnox.se/developer/authorization/get-access-token
    access_token: str
    refresh_token: str
    scope: str
    expires_in: int
    token_type: str


class AccessTokenError(BaseModel):
    # Annoyingly Fortnox uses a different format for their auth API
    # Example response:
    # {'error': 'invalid_grant', 'error_description': "Authorization code doesn't exist or is invalid for the client"}
    error: str
    error_description: str


class AuthCodeGrant(BaseModel):
    code: str
    redirect_uri: str


class RefreshTokenGrant(BaseModel):
    code: str


Grant = Union[AuthCodeGrant, RefreshTokenGrant]


class ExternalAPIError(Exception):
    pass


class Error(BaseModel):
    Code: int
    Error: int
    Message: str


class Me(BaseModel):
    # https://apps.fortnox.se/apidocs#tag/fortnox_Me
    Email: str
    Id: str
    Locale: str | None
    Name: str
    SysAdmin: bool


AuthResponse = Union[AccessTokenResponse, AccessTokenError]


class FortnoxAPIClient:
    """
    A class to interact with Fortnox API.
    """
    API_URL = "https://api.fortnox.se/3"
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

    def get_access_token(self, grant: Grant) -> AccessTokenResponse:
        token_url = f"{self.FORTNOX_URL}/token"
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {'Authorization': f'Basic {encoded_credentials}', 'Content-Type': 'application/x-www-form-urlencoded'}

        match grant:
            case AuthCodeGrant(code=code, redirect_uri=redirect_uri):
                body = {'grant_type': 'authorization_code', 'code': code, 'redirect_uri': redirect_uri, }
            case RefreshTokenGrant(code=code):
                body = {'grant_type': 'refresh_token', 'refresh_token': code, 'client_id': self.client_id, }

        adapter = TypeAdapter(AuthResponse)
        response = requests.post(token_url, headers=headers, data=body)
        match adapter.validate_python(response.json()):
            case AccessTokenResponse(access_token=access_token, refresh_token=refresh_token, scope=scope,
                                     expires_in=expires_in, token_type=token_type):
                return AccessTokenResponse(access_token=access_token, refresh_token=refresh_token, scope=scope,
                                           expires_in=expires_in, token_type=token_type)
            case AccessTokenError(error=_, error_description=desc):
                raise ExternalAPIError(desc)
            case _:
                raise Exception("Unknown error")

    def get_user_info(self, access_token) -> Me:
        response = self.get_api_request(access_token, 'me')
        match response.json():
            case {"Me": data}:
                return Me.model_validate(data)
            case {"Error": data}:
                e = Error.model_validate(data)
                raise ExternalAPIError(e.Message)
            case _:
                raise Exception("Unknown error")

    @classmethod
    def get_api_request(cls, access_token, endpoint):
        headers = {'Authorization': f'Bearer {access_token}'}
        url = f'{cls.API_URL}/{endpoint}'
        return requests.get(f"{cls.API_URL}/{endpoint}", headers=headers)

    @staticmethod
    def get_company_info(access_token):
        company_info_url = 'https://api.fortnox.se/3/companyinformation'
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(company_info_url, headers=headers)
        return response

    @staticmethod
    def get_accounts(access_token, page):
        account_url = 'https://api.fortnox.se/3/accounts?page=' + str(page)
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(account_url, headers=headers)
        return response.json()

    @staticmethod
    def get_voucher_series(access_token):
        voucher_series_url = 'https://api.fortnox.se/3/voucherseries'
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(voucher_series_url, headers=headers)
        return response.json()

    # https://api.fortnox.se/3/costcenters
    @staticmethod
    def get_cost_centers(access_token):
        cost_centers_url = 'https://api.fortnox.se/3/costcenters'
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(cost_centers_url, headers=headers)
