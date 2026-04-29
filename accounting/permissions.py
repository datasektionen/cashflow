from __future__ import annotations

from abc import abstractmethod, ABC
from typing import TYPE_CHECKING

from django.db.models import QuerySet

if TYPE_CHECKING:
    from expenses.models import Expense
    from invoices.models import Invoice
    from django.contrib.auth.models import AbstractBaseUser as User


class AccountingPermissionProvider(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def may_account(self, target: Expense | Invoice, user: User) -> bool:
        pass

    @abstractmethod
    def accountable_expenses(self, user: User) -> QuerySet:
        pass

    @abstractmethod
    def accountable_invoices(self, user: User) -> QuerySet:
        pass
