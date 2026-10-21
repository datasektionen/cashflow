from abc import ABC, abstractmethod
from functools import lru_cache

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.module_loading import import_string

lazy from core.models import Claim, Comment


class NotificationProvider(ABC):
    @abstractmethod
    def on_expense_update(self, expense):
        pass

    @abstractmethod
    def on_invoice_update(self, invoice):
        pass

    @abstractmethod
    def on_comment(self, claim: Claim, comment: Comment):
        pass

    @abstractmethod
    def on_attest(self, claim: Claim, attester: User):
        pass

    @abstractmethod
    def on_confirm(self, claim: Claim, confirmer: User):
        pass

    @abstractmethod
    def on_payment(self, claim: Claim, payer: User):
        pass


@lru_cache(maxsize=1)
def get_notification_provider() -> NotificationProvider:
    return import_string(settings.NOTIFICATION_PROVIDER)()
