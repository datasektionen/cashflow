"""
This module defines Pydantic data modules that are used to
validate and (de)serialize data passed to and from the API.
"""
from typing import Literal, Optional

from pydantic import BaseModel, constr, conint, Field, model_validator


class Account(BaseModel):
    # https://apps.fortnox.se/apidocs#tag/fortnox_Accounts
    url: Optional[str] = Field(alias="@url", default=None)
    Active: Optional[bool] = None
    BalanceBroughtForward: Optional[float] = None
    BalanceCarriedForward: Optional[float] = None
    CostCenter: Optional[str] = None
    CostCenterSettings: Optional[Literal['ALLOWED', 'MANDATORY', 'NOTALLOWED']] = None
    Description: constr(min_length=1, max_length=200)
    Number: conint(ge=1000, le=9999)
    OpeningQuantities: Optional[list[OpeningQuantity]] = None
    Project: Optional[str] = None
    ProjectSettings: Optional[Literal['ALLOWED', 'MANDATORY', 'NOTALLOWED']] = None
    QuantitySettings: Optional[Literal['ALLOWED', 'MANDATORY', 'NOTALLOWED']] = None
    QuantityUnit: Optional[str] = None
    SRU: Optional[int] = None
    TransactionInformation: Optional[str] = None
    TransactionInformationSettings: Optional[Literal['ALLOWED', 'MANDATORY', 'NOTALLOWED']] = None
    VATCode: Optional[str] = None
    Year: Optional[int] = None

    @model_validator(mode='after')
    def verify_settings(self):
        match self.CostCenterSettings, self.CostCenter:
            case 'ALLOWED', _:
                pass
            case 'MANDATORY', None:
                raise ValueError('CostCenter cannot be empty when mandatory')
            case 'NOTALLOWED', c if isinstance(c, str):
                raise ValueError('CostCenter must be None when not allowed')

        match self.ProjectSettings, self.Project:
            case 'ALLOWED', _:
                pass
            case 'MANDATORY', None:
                raise ValueError('Project cannot be empty when mandatory')
            case 'NOTALLOWED', c if isinstance(c, str):
                raise ValueError('Project must be None when not allowed')

        match self.TransactionInformationSettings, self.TransactionInformation:
            case 'ALLOWED', _:
                pass
            case 'MANDATORY', None:
                raise ValueError('TransactionInformation cannot be empty when not allowed')
            case 'NOTALLOWED', c if isinstance(c, str):
                raise ValueError('TransactionInformation must be None when not allowed')

        return self

class AccountsMetaInformation(BaseModel):
    TotalResources: int = Field(alias="@TotalResources")
    TotalPages: int = Field(alias="@TotalPages")
    CurrentPage: int = Field(alias="@CurrentPage")

class Me(BaseModel):
    # https://apps.fortnox.se/apidocs#tag/fortnox_Me
    Email: str
    Id: str
    Locale: str | None
    Name: str
    SysAdmin: bool


class OpeningQuantity(BaseModel):
    Balance: int
    Project: str


class AuthCodeGrant(BaseModel):
    code: str
    redirect_uri: str


class RefreshTokenGrant(BaseModel):
    code: str


class Error(BaseModel):
    Code: int
    Error: int
    Message: str


class AccessTokenResponse(BaseModel):
    # https://www.fortnox.se/developer/authorization/get-access-token
    access_token: str
    refresh_token: str
    scope: str
    expires_in: int
    token_type: str
