from abc import ABC, abstractmethod
from functools import lru_cache

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.module_loading import import_string

lazy from core.models import Claim
lazy from core.models import Comment as CoreComment
lazy from expenses.models import Comment, Expense
lazy from invoices.models import Invoice


class NotificationProvider(ABC):
    @abstractmethod
    def on_expense_update(self, expense):
        pass

    @abstractmethod
    def on_invoice_update(self, invoice):
        pass

    @abstractmethod
    def on_comment(
        self, claim: Expense | Invoice | Claim, comment: Comment | CoreComment
    ):
        pass

    @abstractmethod
    def on_attest(self, claim: Expense | Invoice, attester: User):
        pass

    @abstractmethod
    def on_confirm(self, expense: Expense, confirmer: User):
        pass

    @abstractmethod
    def on_payment(self, claim: Expense | Invoice, payer: User):
        pass


@lru_cache(maxsize=1)
def get_notification_provider() -> NotificationProvider:
    return import_string(settings.NOTIFICATION_PROVIDER)()
