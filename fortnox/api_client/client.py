import base64
import logging
from enum import Enum
from typing import Union, Literal, Any, Optional, Callable
from urllib import parse

import requests
from pydantic import BaseModel, TypeAdapter, RootModel, Field

from fortnox.api_client.exceptions import CODE_EXCEPTION_MAPPING, FortnoxAPIError, ResponseParsingError, \
    FortnoxNotFound, FortnoxAuthenticationError
from fortnox.api_client.models import Me, AuthCodeGrant, RefreshTokenGrant, Error, AccessTokenResponse, Account, \
    ListMetaInformaion, CostCenter, CompanyInformation, VoucherSeriesListItem, VoucherSeries, Expense, Voucher, \
    VoucherCreate, FinancialYear

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
                 access_type: Literal['offline'] = 'offline', token_provider: Callable = None):
        self.client_id = client_id
        self.client_secret = client_secret
        # Ensure valid scopes to prevent future errors
        self.scope = TypeAdapter(list[self._ScopeEnum]).validate_python(scope)
        self.access_type = access_type
        self.token_provider = token_provider

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
                raise FortnoxAuthenticationError(f'{e.error}: {e.error_description}')
            case _:
                raise ResponseParsingError("Unknown or invalid API response from Fortnox")

    # ======================
    # Accounts
    # ======================

    def list_accounts(self, access_token: str = None, limit: int = 100, page: int = 1) -> list[Account]:
        response = self._get("accounts", parameters={"limit": limit, "page": page}, access_token=access_token)
        return self._parse_list_response(response, Account, "Accounts")[0]

    def retrieve_account(self, number: int, access_token: str = None) -> Account:
        response = self._get(f"accounts/{number}", access_token=access_token)
        return self._parse_retrieve_response(response, Account, "Account")

    # ======================
    # Cost centers
    # ======================

    def list_cost_centers(self, access_token: str = None, limit: int = 100, page: int = 1) -> list[CostCenter]:
        response = self._get("costcenters", {"limit": limit, "page": page}, access_token=access_token)
        return self._parse_list_response(response, CostCenter, "CostCenters")[0]

    def find_cost_center(self, access_token: str = None, **fields) -> CostCenter:
        """Finds the first cost center on Fortnox that matches the given fields."""
        page = 1
        while True:
            response = self._get("costcenters", parameters={"page": page}, access_token=access_token)
            data, meta = self._parse_list_response(response, CostCenter, "CostCenters")
            page = meta.CurrentPage
            for cc in data:
                cc_data = cc.model_dump()

                # Check that given fields match
                if all(cc_data.get(k) == v for k, v in fields.items()):
                    return cc

            if page >= meta.TotalPages:
                break

        raise FortnoxNotFound(f"Could not find a cost center matching {fields}")

    # ======================
    # Company information
    # ======================

    def retrieve_company_info(self, access_token: str = None) -> CompanyInformation:
        response = self._get("companyinformation", access_token=access_token)
        return self._parse_retrieve_response(response, CompanyInformation, "CompanyInformation")

    # ======================
    # Expenses
    # ======================

    def list_expenses(self, access_token: str = None, limit: int = 100, page: int = 1) -> list[Expense]:
        response = self._get("expenses", parameters={"limit": limit, "page": page}, access_token=access_token)
        return self._parse_list_response(response, Expense, "Expenses")[0]

    def retrieve_expense(self, code: str, access_token: str = None) -> Expense:
        response = self._get(f"expenses/{code}", access_token=access_token)
        return self._parse_retrieve_response(response, Expense, "Expense")

    # ======================
    # Financial years
    # ======================

    def list_financial_years(self, access_token: str = None, limit: int = 100, page: int = 1) -> list[FinancialYear]:
        response = self._get("financialyears", parameters={"limit": limit, "page": page}, access_token=access_token)
        return self._parse_list_response(response, FinancialYear, "FinancialYears")[0]

    def retrieve_financial_year(self, id: int, access_token: str = None) -> FinancialYear:
        response = self._get(f"financialyears/{id}", access_token=access_token)
        return self._parse_retrieve_response(response, FinancialYear, "FinancialYear")

    # ======================
    # Users
    # ======================

    def retrieve_current_user(self, access_token: str = None) -> Me:
        """Retrieves information about the user connected to the given token"""
        try:
            response = self._get('me', access_token=access_token)
        except FortnoxNotFound as e:
            raise FortnoxNotFound("No user connected to the given token.") from e
        return self._parse_retrieve_response(response, Me, "Me")

    # ======================
    # Vouchers
    # ======================

    def list_vouchers(self, limit: int = 100, page: int = 1, access_token: str = None) -> list[Voucher]:
        response = self._get("vouchers", parameters={"limit": limit, "page": page}, access_token=access_token)
        return self._parse_list_response(response, Voucher, "Vouchers")[0]

    def retrieve_voucher(self, voucher_series: str, voucher_number: int, access_token: str = None) -> Voucher:
        response = self._get(f"vouchers/{voucher_series}/{voucher_number}", access_token=access_token)
        return self._parse_retrieve_response(response, Voucher, "Voucher")

    def create_voucher(self, voucher: Optional[VoucherCreate] = None, access_token: str = None, **fields) -> Voucher:
        if voucher is None:
            voucher = VoucherCreate(**fields)
        # Using by_alias and exclude_none is important!
        # The API expects the url field to be "@url" and that no None-fields are included
        model_dict = voucher.model_dump(by_alias=True, exclude_none=True)
        response = self._post("vouchers", json={"Voucher": model_dict}, access_token=access_token)
        return self._parse_retrieve_response(response, Voucher, "Voucher")

    def list_voucher_series(self, limit: int = 100, page: int = 1, access_token: str = None) -> list[
        VoucherSeriesListItem]:
        response = self._get("voucherseries", parameters={"limit": limit, "page": page}, access_token=access_token)
        return self._parse_list_response(response, VoucherSeriesListItem, "VoucherSeriesCollection")[0]

    def retrieve_voucher_series(self, code: str, access_token: str = None) -> VoucherSeries:
        response = self._get(f"voucherseries/{code}", access_token=access_token)
        return self._parse_retrieve_response(response, VoucherSeries, "VoucherSeries")

    # ======================
    # Helpers
    # ======================

    @classmethod
    def _parse_retrieve_response[T](cls, response: requests.Response, model: type[T], label: str) -> T:
        data = cls._validate(model, response)
        if isinstance(data.get(label), model):
            return data[label]
        elif isinstance(data.get("ErrorInformation"), Error):
            raise cls._parse_error(data["ErrorInformation"])
        else:
            raise ResponseParsingError("Unknown or invalid API response from Fortnox")

    @classmethod
    def _parse_list_response[T](cls, response: requests.Response, model: type[T], label: str) -> tuple[
        list[T], ListMetaInformaion]:
        class ResponseModel(BaseModel):
            MetaInformation: ListMetaInformaion
            Collection: list[model] = Field(alias=label)

        adapter = TypeAdapter(Union[ResponseModel, Error])

        match adapter.validate_python(response.json()):
            case ResponseModel() as resp:
                return resp.Collection, resp.MetaInformation
            case Error() as e:
                raise cls._parse_error(e)
            case _:
                raise ResponseParsingError("Unknown or invalid API response from Fortnox")

    def _get(self, endpoint: str, parameters: dict[str, Any] = None, access_token: str = None) -> requests.Response:
        """Performs a GET request to a Fortnox API endpoint, returning a response object"""

        if access_token is None:
            access_token = self.token_provider()

        headers = {'Authorization': f'Bearer {access_token}'}
        url_params = "?" + parse.urlencode(parameters) if parameters is not None else ""
        response = requests.get(f"{self.API_URL}/{endpoint}/{url_params}", headers=headers)
        logger.debug(response)

        # TODO: Handle more errors
        if response.status_code != 200:

            if response.status_code == 401:
                raise FortnoxAuthenticationError("Invalid access token")
            elif response.status_code == 404:
                raise FortnoxNotFound("Resource not found")

            # Fortnox doesn't seem to be consistent with their HTTP error codes
            # For example, trying to access something without proper authentication
            # will produce a 400 response, instead of 403
            #   They do, however, send error information which we can parse to raise proper
            # exceptions.

            # Try to parse error
            try:
                error = Error.model_validate(response.json()["ErrorInformation"])
                raise self._parse_error(error)
            except Exception:
                raise FortnoxAPIError(
                    f"Unknown error from Fortnox API, failed to parse error response:\n{response.text=}")

        return response

    def _post(self, endpoint: str, json: dict, access_token: str = None):
        if access_token is None:
            access_token = self.token_provider()
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.post(f"{self.API_URL}/{endpoint}/", json=json, headers=headers)
        logger.debug(response)
        return response

    # Helper to validate API responses against models
    @classmethod
    def _validate(cls, model, response):
        # response -> InfoModel or Error
        return cls._APIResponse[Union[model, Error]].model_validate(response.json()).root

    # This class should only be used internally,
    # it's constructed to neatly parse the JSON responses from Fortnox
    class _APIResponse[InfoModel](RootModel[dict[str, InfoModel]]):
        # Responses from Fortnox come in the following shape:
        # {
        #   "Model": {
        #       ...
        #   }
        # }
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

    @classmethod
    def _parse_error(cls, error: Error) -> Exception:
        # Takes an ErrorInformation object and tries to generate a suitable exception
        exception = CODE_EXCEPTION_MAPPING.get(error.Code)
        if exception is not None:
            return exception
        else:
            return FortnoxAPIError(f"Unknown error from Fortnox API ({error.Code=}):\n{error.Message}")
