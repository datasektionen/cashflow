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


class PermissionProvider(ABC):

    @abstractmethod
    def may_view_all(self, user: User) -> bool:
        pass

    @abstractmethod
    def may_view_all_payments(self, user: User) -> bool:
        pass

    @abstractmethod
    def viewable_cost_centres(self, user: User) -> list[str]:
        """Cost centres the user has scoped view-expenses access to."""
        pass

    @abstractmethod
    def may_attest(self, user: User, cost_centre: str) -> bool:
        pass

    @abstractmethod
    def may_attest_some(self, user: User) -> bool:
        pass

    @abstractmethod
    def attestable_cost_centres(self, user: User) -> list[str]:
        pass

    @abstractmethod
    def may_unattest(self, user: User) -> bool:
        pass

    @abstractmethod
    def may_confirm(self, user: User) -> bool:
        pass

    @abstractmethod
    def may_account(self, user: User, target: Expense | Invoice) -> bool:
        pass

    @abstractmethod
    def may_account_some(self, user: User) -> bool:
        pass

    @abstractmethod
    def may_account_cost_centre(self, user: User, cost_centre: str) -> bool:
        pass

    @abstractmethod
    def accountable_cost_centres(self, user: User) -> list[str]:
        pass

    @abstractmethod
    def accountable_expenses(self, user: User) -> QuerySet:
        pass

    @abstractmethod
    def accountable_invoices(self, user: User) -> QuerySet:
        pass

    @abstractmethod
    def may_pay(self, user: User) -> bool:
        pass

    @abstractmethod
    def may_delete(self, user: User) -> bool:
        pass

    @abstractmethod
    def may_edit_invoice(self, user: User) -> bool:
        pass

    @abstractmethod
    def may_moderate_comments(self, user: User) -> bool:
        pass

    @abstractmethod
    def may_firmatecknare(self, user: User) -> bool:
        pass

    @abstractmethod
    def may_view_account(self, user: User) -> bool:
        pass


@lru_cache(maxsize=1)
def get_permission_provider() -> PermissionProvider:
    return import_string(settings.PERMISSION_PROVIDER)()
