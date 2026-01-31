from typing import Literal, Optional

from pydantic import BaseModel, constr, conint, model_validator


class Account(BaseModel):
    # https://apps.fortnox.se/apidocs#tag/fortnox_Accounts
    url: Optional[str]
    Active: Optional[bool]
    BalanceBroughtForward: Optional[float]
    BalanceCarriedForward: Optional[float]
    CostCenter: Optional[str]
    CostCenterSettings: Optional[Literal['ALLOWED', 'MANDATORY', 'NOTALLOWED']]
    Description: constr(min_length=1, max_length=200)
    Number: conint(ge=1000, le=9999)
    OpeningQuantities: Optional[list[OpeningQuantity]]
    Project: Optional[str]
    ProjectSettings: Optional[Literal['ALLOWED', 'MANDATORY', 'NOTALLOWED']]
    QuantitySettings: Optional[Literal['ALLOWED', 'MANDATORY', 'NOTALLOWED']]
    QuantityUnit: Optional[str]
    SRU: Optional[int]
    TransactionInformation: Optional[str]
    TransactionInformationSettings: Optional[Literal['ALLOWED', 'MANDATORY', 'NOTALLOWED']]
    VATCode: Optional[str]
    Year: Optional[int]

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
