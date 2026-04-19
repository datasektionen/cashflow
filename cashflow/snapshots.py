"""This file defines serialization formats for snapshots.

Snapshots are used to keep historical information from when an expense/invoice is processed.
While all expenses and invoices has a GOrdian reference id it is not guaranteed to stay the same forever,
so for archiving/auditing reasons we want to store the exact information that was originally created.
"""

from datetime import datetime
from typing import Literal, Final

from pydantic import BaseModel
from pydantic import ConfigDict

CURRENT_SCHEMA_VERSION: Final = 1


# == General information ==
class Budgetline(BaseModel):
    name: str
    cost_center: str
    secondary_cost_center: str


class Owner(BaseModel):
    name: str
    email: str


# == Expenses ==
class ExpensePartSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: Final[int] = CURRENT_SCHEMA_VERSION
    captured_at: datetime
    budget_line: Budgetline


class ExpenseSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: Final[int] = CURRENT_SCHEMA_VERSION
    captured_at: datetime
    owner: Owner


# == Invoices ==
class InvoicePartSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: Final[int] = CURRENT_SCHEMA_VERSION
    captured_at: datetime
    budget_line: Budgetline


class InvoiceSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: Final[1] = CURRENT_SCHEMA_VERSION
    captured_at: datetime
    owner: Owner
