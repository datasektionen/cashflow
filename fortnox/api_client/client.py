import base64
import logging
from enum import Enum
from typing import Union, Literal

import requests
from pydantic import BaseModel, TypeAdapter, RootModel

from fortnox.api_client.exceptions import FortnoxAPIError, ResponseParsingError
from fortnox.api_client.models import Me, AuthCodeGrant, RefreshTokenGrant, Error, AccessTokenResponse

logger = logging.getLogger(__name__)


class FortnoxAPIClient:
    """HTTP client for the Fortnox API.

    This class encapsulates configuration against a Fortnox integration,
    as well as request serialization and response deserialization. It does not
    handle storing user credentials; access tokens must be passed as method arguments.


    """
    API_URL = "https://api.fortnox.se/3"
    FORTNOX_URL = "https://apps.fortnox.se/oauth-v1"

    # This class should only be used internally,
    # it's constructed to neatly parse the JSON responses from Fortnox
    class _APIResponse[InfoModel](RootModel[dict[str, InfoModel]]):
        pass

    class _AuthErrorInfo(BaseModel):
        # Annoyingly Fortnox uses a different format for their auth API
        # Example response:
        # {'error': 'invalid_grant', 'error_description': "Authorization code doesn't exist or is invalid for the client"}
        error: str
        error_description: str

    # TODO: Should this be "publicly" available?
    class _ScopeEnum(str, Enum):
        salary = 'salary'
        bookkeeping = 'bookkeeping'
        archive = 'archive'
        connectfile = 'connectfile'
        article = 'article'
        assets = 'assets'
        companyinformation = 'companyinformation'
        settings = 'settings'
        invoice = 'invoice'
        costcenter = 'costcenter'
        currency = 'currency'
        customer = 'customer'
        inbox = 'inbox'
        payment = 'payment'
        noxfinansinvoice = 'noxfinansinvoice'
        offer = 'offer'
        order = 'order'
        price = 'price'
        print = 'print'
        project = 'project'
        profile = 'profile'
        supplierinvoice = 'supplierinvoice'
        supplier = 'supplier'
        timereporting = 'timereporting'

    def __init__(self, client_id: str, client_secret: str, scope: list[str],
                 access_type: Literal['offline'] = 'offline'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = list[self._ScopeEnum](scope)
        self.access_type = access_type

    # Helper to validate API responses against models
    @classmethod
    def _validate(cls, model, response):
        return cls._APIResponse[Union[model, Error]].model_validate(response.json()).root

    def get_auth_code_url(self, redirect_uri, state):
        """
        Returns an authorization URL, with suitable parameters, based on the
        redirect URI and state.
        """
        # https://www.fortnox.se/developer/authorization/get-authorization-code
        return f"{self.FORTNOX_URL}/auth?client_id={self.client_id}&redirect_uri={redirect_uri}&scope={'%'.join(self.scope)}&state={state}&access_type={self.access_type}&response_type=code&account_type=service"

    def get_access_token(self, grant: Union[AuthCodeGrant, RefreshTokenGrant]) -> AccessTokenResponse:
        """Requests a new access token for a user.

        A new access token can be requested using an auth code or refresh token.
        The suitable grant type (AuthCodeGrant or RefreshTokenGrant) must be used
        in the method arguments.
        """
        token_url = f"{self.FORTNOX_URL}/token"
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {'Authorization': f'Basic {encoded_credentials}', 'Content-Type': 'application/x-www-form-urlencoded'}

        # Use authorization code or refresh token to fetch access_token
        match grant:
            case AuthCodeGrant(code=code, redirect_uri=redirect_uri):
                body = {'grant_type': 'authorization_code', 'code': code, 'redirect_uri': redirect_uri, }
            case RefreshTokenGrant(code=code):
                body = {'grant_type': 'refresh_token', 'refresh_token': code, 'client_id': self.client_id, }

        # Parse/deserialize response or error
        response = requests.post(token_url, headers=headers, data=body)
        adapter = TypeAdapter(Union[AccessTokenResponse, self._AuthErrorInfo])
        match adapter.validate_python(response.json()):
            case AccessTokenResponse() as response:
                if logger.level == 'DEBUG':
                    user_info = self.get_user_info(response.access_token)
                    logger.debug(f'{user_info.Name} fetched new access token')
                return response
            case self._AuthErrorInfo() as e:
                raise FortnoxAPIError(f'{e.error}: {e.error_description}')
            case _:
                raise ResponseParsingError("Unknown or invalid API response from Fortnox")

    def get_user_info(self, access_token) -> Me:
        """Retrieves information about the user connected to the given token"""
        response = self.get_api_request(access_token, 'me')
        match self._validate(Me, response):
            case {'Me': Me() as me}:
                return me
            case {'Error': Error(_, description)}:
                raise FortnoxAPIError(description)
            case _:
                raise ResponseParsingError("Unknown or invalid API response from Fortnox")

    @classmethod
    def get_api_request(cls, access_token: str, endpoint: str) -> requests.Response:
        """Performs a GET request to a Fortnox API endpoint, returning a response object"""
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f"{cls.API_URL}/{endpoint}", headers=headers)

        # TODO: Better error handling
        if response.status_code != 200:
            raise FortnoxAPIError(response.text)
        return response

    # TODO: These methods need to be updated, and will probably not work as expected
    @staticmethod
    def get_company_info(access_token):
        logger.warning('get_company is deprecated')
        company_info_url = 'https://api.fortnox.se/3/companyinformation'
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(company_info_url, headers=headers)

    @staticmethod
    def get_accounts(access_token, page):
        logger.warning('get_company is deprecated')
        account_url = 'https://api.fortnox.se/3/accounts?page=' + str(page)
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(account_url, headers=headers)
        return response.json()

    @staticmethod
    def get_voucher_series(access_token):
        logger.warning('get_company is deprecated')
        voucher_series_url = 'https://api.fortnox.se/3/voucherseries'
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(voucher_series_url, headers=headers)
        return response.json()

    # https://api.fortnox.se/3/costcenters
    @staticmethod
    def get_cost_centers(access_token):
        logger.warning('get_company is deprecated')
        cost_centers_url = 'https://api.fortnox.se/3/costcenters'
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(cost_centers_url, headers=headers)
