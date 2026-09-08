from abc import ABC, abstractmethod
from functools import lru_cache
from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.utils.module_loading import import_string

from django.conf import settings

if TYPE_CHECKING:
    from expenses.models import Expense, Comment
    from invoices.models import Invoice


class NotificationProvider(ABC):

    @abstractmethod
    def on_expense_update(self, expense):
        pass

    @abstractmethod
    def on_invoice_update(self, invoice):
        pass

    @abstractmethod
    def on_comment(self, claim: "Expense | Invoice", comment: "Comment"):
        pass

    @abstractmethod
    def on_attest(self, claim: "Expense | Invoice", attester: User):
        pass

    @abstractmethod
    def on_confirm(self, expense: "Expense", confirmer: User):
        pass

    @abstractmethod
    def on_payment(self, claim: "Expense | Invoice", payer: User):
        pass


@lru_cache(maxsize=1)
def get_notification_provider() -> NotificationProvider:
    return import_string(settings.NOTIFICATION_PROVIDER)()
