"""
This module defines Pydantic data modules that are used to
validate and (de)serialize data passed to and from the API.
"""
from typing import Literal, Optional

from pydantic import BaseModel, constr, conint, Field, AliasChoices


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


class AccountsMetaInformation(BaseModel):
    TotalResources: int = Field(alias="@TotalResources")
    TotalPages: int = Field(alias="@TotalPages")
    CurrentPage: int = Field(alias="@CurrentPage")


class CompanyInformation(BaseModel):
    Address: Optional[str] = None
    City: Optional[str] = None
    CompanyName: Optional[str] = None
    CountryCode: Optional[str] = None
    DatabaseNumber: Optional[int] = None
    OrganizationNumber: Optional[str] = None
    VisitAddress: Optional[str] = None
    VisitCity: Optional[str] = None
    VisitCountryCode: Optional[str] = None
    VisitZipCode: Optional[str] = None
    ZipCode: Optional[str] = None


class CostCenter(BaseModel):
    url: Optional[str] = Field(alias="@url", default=None)
    Active: Optional[bool] = None
    Code: constr(min_length=1, max_length=6)
    Description: constr(min_length=1)
    Note: Optional[str] = None


class Expense(BaseModel):
    url: Optional[str] = Field(alias="@url", default=None)
    Account: int
    Code: str
    Text: str


class Me(BaseModel):
    # https://apps.fortnox.se/apidocs#tag/fortnox_Me
    Email: str
    Id: str
    Locale: str | None
    Name: str
    SysAdmin: bool


class VoucherSeries(BaseModel):
    class ApproverModel(BaseModel):
        Id: int
        Name: str

    url: Optional[str] = Field(alias="@url", default=None)
    Approver: Optional[ApproverModel] = None
    Code: constr(min_length=1, max_length=10)
    Description: Optional[constr(max_length=200)] = None
    Manual: Optional[bool] = None
    NextVoucherNumber: Optional[int] = None
    Year: Optional[int] = None


class VoucherSeriesListItem(BaseModel):
    url: Optional[str] = Field(alias="@url", default=None)
    Approver: Optional[VoucherSeries.ApproverModel] = None
    Code: constr(min_length=1, max_length=10)
    Description: Optional[constr(max_length=200)]
    Manual: Optional[bool] = None
    Year: Optional[int] = None


class OpeningQuantity(BaseModel):
    Balance: int
    Project: str


class AuthCodeGrant(BaseModel):
    code: str
    redirect_uri: str


class RefreshTokenGrant(BaseModel):
    code: str


class Error(BaseModel):
    # Fortnox is very inconsistent with casing, hence multiple aliases
    Error: int = Field(validation_alias=AliasChoices("Error", "error"))
    Message: str = Field(validation_alias=AliasChoices("Message", "message"))
    Code: int = Field(validation_alias=AliasChoices("Code", "code"))


class AccessTokenResponse(BaseModel):
    # https://www.fortnox.se/developer/authorization/get-access-token
    access_token: str
    refresh_token: str
    scope: str
    expires_in: int
    token_type: str
