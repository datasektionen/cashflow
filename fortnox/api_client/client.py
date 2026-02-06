import base64
import logging
from enum import Enum
from typing import Union, Literal, Any
from urllib import parse

import requests
from pydantic import BaseModel, TypeAdapter, RootModel

from fortnox.api_client.exceptions import FortnoxAPIError, ResponseParsingError, FortnoxPermissionDenied, \
    FortnoxNotFound, FortnoxAuthenticationError
from fortnox.api_client.models import Me, AuthCodeGrant, RefreshTokenGrant, Error, AccessTokenResponse, Account, \
    ListMetaInformaion, CostCenter, CompanyInformation, VoucherSeriesListItem, VoucherSeries, Expense

logger = logging.getLogger(__name__)


class FortnoxAPIClient:
    """HTTP client for the Fortnox API.

    This class encapsulates configuration against a Fortnox integration,
    as well as request serialization and response deserialization. It does not
    handle storing user credentials; access tokens must be passed as method arguments.
    """
    API_URL = "https://api.fortnox.se/3"
    FORTNOX_URL = "https://apps.fortnox.se/oauth-v1"

    def __init__(self, client_id: str, client_secret: str, scope: list[str],
                 access_type: Literal['offline'] = 'offline'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = list[self._ScopeEnum](scope)
        self.access_type = access_type

    # ======================
    # Authentication
    # ======================

    def build_auth_code_url(self, redirect_uri, state):
        """
        Returns an authorization URL, with suitable parameters, based on the
        redirect URI and state.
        """
        # https://www.fortnox.se/developer/authorization/get-authorization-code
        return f"{self.FORTNOX_URL}/auth?client_id={self.client_id}&redirect_uri={parse.quote_plus(redirect_uri)}&scope={'%20'.join(self.scope)}&state={state}&access_type={self.access_type}&response_type=code&account_type=service"

    def retrieve_access_token(self, grant: Union[AuthCodeGrant, RefreshTokenGrant]) -> AccessTokenResponse:
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
                    user_info = self.retrieve_current_user(response.access_token)
                    logger.debug(f'{user_info.Name} fetched new access token')
                return response
            case self._AuthErrorInfo() as e:
                raise FortnoxAPIError(f'{e.error}: {e.error_description}')
            case _:
                raise ResponseParsingError("Unknown or invalid API response from Fortnox")

    # ======================
    # Accounts
    # ======================

    def list_accounts(self, access_token: str, sru: int | None = None, orderby: Literal["number"] = "number",
                      limit: int = 100, page: int = 1) -> list[Account]:
        response = self._get(access_token, "accounts", parameters={"limit": limit, "page": page})

        class ResponseModel(BaseModel):
            MetaInformation: ListMetaInformaion
            Accounts: list[Account]

        adapter = TypeAdapter(Union[ResponseModel, Error])
        data = adapter.validate_python(response.json())
        match data:
            case ResponseModel():
                return data.Accounts
            case Error(_, description):
                raise FortnoxAPIError(description)
            case _:
                raise ResponseParsingError("Unknown or invalid API response from Fortnox")

    def retrieve_account(self, access_token: str, number: int) -> Account:
        response = self._get(access_token, f"accounts/{number}")
        match self._validate(Account, response):
            case {"Account": Account() as account}:
                return account
            case {"Error": Error(_, description)}:
                raise FortnoxAPIError(description)
            case _:
                raise ResponseParsingError("Unknown or invalid API response from Fortnox")

    # ======================
    # Cost centers
    # ======================

    def list_cost_centers(self, access_token: str, limit: int = 100, page: int = 1) -> list[CostCenter]:
        response = self._get(access_token, "costcenters", {"limit": limit, "page": page})

        class ResponseModel(BaseModel):
            CostCenters: list[CostCenter]

        adapter = TypeAdapter(Union[ResponseModel, Error])
        data = adapter.validate_python(response.json())
        if isinstance(data, ResponseModel):
            return data.CostCenters
        elif isinstance(data, Error):
            logger.debug(data)
            raise FortnoxAPIError(f"{data.Error}: {data.Message}")
        raise ResponseParsingError("Unknown or invalid API response from Fortnox")

    # ======================
    # Company information
    # ======================
    def retrieve_company_info(self, access_token: str) -> CompanyInformation:
        response = self._get(access_token, "companyinformation")
        match self._validate(CompanyInformation, response):
            case {"CompanyInformation": CompanyInformation() as c}:
                return c
            case {"Error": Error(_, description)}:
                raise FortnoxAPIError(description)
            case _:
                raise ResponseParsingError("Unknown or invalid API response from Fortnox")

    # ======================
    # Expenses
    # ======================

    def retrieve_expense(self, code: str) -> Expense:
        response = self._get(code, f"expenses/{code}")

        match self._validate(Expense, response):
            case {"Expense": Expense() as expense}:
                return expense
            case {"Error": Error(_, description)}:
                raise FortnoxAPIError(description)
            case _:
                raise ResponseParsingError("Unknown or invalid API response from Fortnox")

    def list_expenses(self, access_token: str) -> list[Expense]:
        response = self._get(access_token, "expenses")

        class ResponseModel(BaseModel):
            MetaInformation: ListMetaInformaion
            Expenses: list[Expense]

        adapter = TypeAdapter(Union[ResponseModel, Error])
        data = adapter.validate_python(response.json())

        match data:
            case ResponseModel() as resp:
                return resp.Expenses
            case Error(_, description):
                raise FortnoxAPIError(description)
            case _:
                raise ResponseParsingError("Unknown or invalid API response from Fortnox")

    # ======================
    # Users
    # ======================

    def retrieve_current_user(self, access_token: str) -> Me:
        """Retrieves information about the user connected to the given token"""
        response = self._get(access_token, 'me')
        match self._validate(Me, response):
            case {'Me': Me() as me}:
                return me
            case {'Error': Error(_, description)}:
                raise FortnoxAPIError(description)
            case _:
                raise ResponseParsingError("Unknown or invalid API response from Fortnox")

    # ======================
    # Vouchers
    # ======================

    def list_voucher_series(self, access_token: str) -> list[VoucherSeriesListItem]:
        response = self._get(access_token, "voucherseries")

        class ResponseModel(BaseModel):
            MetaInformation: ListMetaInformaion
            VoucherSeriesCollection: list[VoucherSeriesListItem]

        adapter = TypeAdapter(Union[ResponseModel, Error])
        data = adapter.validate_python(response.json())

        match data:
            case ResponseModel() as resp:
                return resp.VoucherSeriesCollection
            case Error(_, description):
                raise FortnoxAPIError(description)
            case _:
                raise ResponseParsingError("Unknown or invalid API response from Fortnox")

    def retrieve_voucher_series(self, access_token: str, code: str) -> VoucherSeries:
        response = self._get(access_token, f"voucherseries/{code}")
        match self._validate(VoucherSeries, response):
            case {"VoucherSeries": VoucherSeries() as vs}:
                return vs
            case {"Error": Error(_, description)}:
                raise FortnoxAPIError(description)
            case _:
                raise ResponseParsingError("Unknown or invalid API response from Fortnox")

    # ======================
    # Helpers
    # ======================

    @classmethod
    def _get(cls, access_token: str, endpoint: str, parameters: dict[str, Any] = None) -> requests.Response:
        """Performs a GET request to a Fortnox API endpoint, returning a response object"""
        headers = {'Authorization': f'Bearer {access_token}'}
        url_params = "?" + parse.urlencode(parameters) if parameters is not None else ""
        response = requests.get(f"{cls.API_URL}/{endpoint}/{url_params}", headers=headers)
        logger.debug(response)

        # TODO: Handle more errors
        if response.status_code != 200:

            if response.status_code == 401:
                raise FortnoxAuthenticationError("Invalid access token")

            # Fortnox doesn't seem to be consistent with their HTTP error codes
            # For example, trying to access something without proper authentication
            # will produce a 400 response, instead of 403
            #   They do, however, send error information which we can parse to raise proper
            # exceptions.

            # Try to parse error
            error = Error.model_validate(response.json()["ErrorInformation"])
            match error:
                case Error(Error=_, Message=msg, Code=2000423):
                    # Resource not found
                    raise FortnoxNotFound(msg)
                case Error(Error=_, Message=msg, Code=2000663):
                    # Insufficient permissions
                    raise FortnoxPermissionDenied(msg)
                case Error(Error=_, Message=msg, Code=2000311):
                    # Missing token/secret
                    raise FortnoxAuthenticationError(msg)
                case _:
                    raise FortnoxAPIError(response.text)

        return response

    # Helper to validate API responses against models
    @classmethod
    def _validate(cls, model, response):
        # response -> InfoModel or Error
        return cls._APIResponse[Union[model, Error]].model_validate(response.json()).root

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
