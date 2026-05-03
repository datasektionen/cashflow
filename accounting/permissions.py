from __future__ import annotations

from abc import abstractmethod, ABC
from functools import lru_cache
from typing import TYPE_CHECKING

from django.conf import settings
from django.db.models import QuerySet
from django.utils.module_loading import import_string

if TYPE_CHECKING:
    from expenses.models import Expense
    from invoices.models import Invoice
    from django.contrib.auth.models import AbstractBaseUser as User


class AccountingPermissionProvider(ABC):

    @abstractmethod
    def may_account(self, target: Expense | Invoice, user: User) -> bool:
        pass

    @abstractmethod
    def accountable_expenses(self, user: User) -> QuerySet:
        pass

    @abstractmethod
    def accountable_invoices(self, user: User) -> QuerySet:
        pass


# The LRU-cache decorator limits the provider to one instance per process
@lru_cache(maxsize=1)
def get_permission_provider() -> AccountingPermissionProvider:
    return import_string(settings.ACCOUNTING_PERMISSION_PROVIDER)()
