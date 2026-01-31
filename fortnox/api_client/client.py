import base64
from typing import Union

import requests
from pydantic import BaseModel, TypeAdapter, RootModel

from fortnox.api_client.models import Me, AuthCodeGrant, RefreshTokenGrant, Error


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


class ExternalAPIError(Exception):
    pass


class FortnoxAPIClient:
    """
    A class to interact with Fortnox API.
    """
    API_URL = "https://api.fortnox.se/3"
    FORTNOX_URL = "https://apps.fortnox.se/oauth-v1"

    AuthResponse = Union[AccessTokenResponse, AccessTokenError]

    # This class should only be used internally,
    # it's constructed to neatly parse the JSON responses from Fortnox
    class ApiResponse[InfoModel](RootModel[dict[str, InfoModel]]):
        pass

    def __init__(self, client_id, client_secret, scope, access_type='offline'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.access_type = access_type

    # Helper to validate API responses against models
    @classmethod
    def _validate(cls, model, response):
        return cls.ApiResponse[Union[model, Error]].model_validate(response.json()).root

    def get_auth_code_url(self, redirect_uri, state):
        # According to the API documentation, you always
        # have to use the same redirect uri that you used
        # when getting the auth code, so we save it
        # https://www.fortnox.se/developer/authorization/get-access-token

        return f"{self.FORTNOX_URL}/auth?client_id={self.client_id}&redirect_uri={redirect_uri}&scope={self.scope}&state={state}&access_type={self.access_type}&response_type=code&account_type=service"

    def get_access_token(self, grant: Union[AuthCodeGrant, RefreshTokenGrant]) -> AccessTokenResponse:
        token_url = f"{self.FORTNOX_URL}/token"
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {'Authorization': f'Basic {encoded_credentials}', 'Content-Type': 'application/x-www-form-urlencoded'}

        match grant:
            case AuthCodeGrant(code=code, redirect_uri=redirect_uri):
                body = {'grant_type': 'authorization_code', 'code': code, 'redirect_uri': redirect_uri, }
            case RefreshTokenGrant(code=code):
                body = {'grant_type': 'refresh_token', 'refresh_token': code, 'client_id': self.client_id, }

        response = requests.post(token_url, headers=headers, data=body)
        adapter = TypeAdapter(self.AuthResponse)
        match adapter.validate_python(response.json()):
            case AccessTokenResponse(access_token=access_token, refresh_token=refresh_token, scope=scope,
                                     expires_in=expires_in, token_type=token_type):
                return AccessTokenResponse(access_token=access_token, refresh_token=refresh_token, scope=scope,
                                           expires_in=expires_in, token_type=token_type)
            case AccessTokenError(error=_, error_description=desc):
                raise ExternalAPIError(desc)
            case _:
                raise ExternalAPIError("Unknown or invalid API response from Fortnox")

    def get_user_info(self, access_token) -> Me:
        response = self.get_api_request(access_token, 'me')
        match self._validate(Me, response):
            case {'Me': Me() as me}:
                return me
            case {'Error': Error(_, description)}:
                raise ExternalAPIError(description)
            case _:
                raise ExternalAPIError("Unknown or invalid API response from Fortnox")

    @classmethod
    def get_api_request(cls, access_token, endpoint):
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f"{cls.API_URL}/{endpoint}", headers=headers)

        # TODO: Better error handling
        if response.status_code != 200:
            raise ExternalAPIError(response.text)
        return response

    @staticmethod
    def get_company_info(access_token):
        company_info_url = 'https://api.fortnox.se/3/companyinformation'
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(company_info_url, headers=headers)


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
