import json
from enum import Enum

import requests
from django.conf import settings
from django.contrib.auth.models import User, AbstractBaseUser
from django.db.models import QuerySet
from pydantic import BaseModel

from mozilla_django_oidc.auth import OIDCAuthenticationBackend

import accounting.permissions


class Permission(str, Enum):
    ACCOUNTING = "accounting"
    ATTEST = "attest"
    CONFIRM = "confirm"
    DELETE = "delete"
    EDIT_INVOICE = "edit-invoice"
    MODERATE_COMMENTS = "moderate-comments"
    PAY = "pay"
    UNATTEST = "unattest"
    UNCONFIRM = "unconfirm"
    VIEW_ALL_PAYMENTS = "view-all-payments"
    VIEW_EXPENSES = "view-expenses"


class HivePermission(BaseModel):
    id: Permission
    scope: bool | list[str]


class Hive(accounting.permissions.AccountingPermissionProvider):

    def _get_accounting_scopes(self, user: User) -> list[str]:
        return get_permissions(user).get(Permission.ACCOUNTING, [])

    def may_account(self, target, user) -> bool:
        from expenses.models import Expense
        from invoices.models import Invoice

        scopes = self._get_accounting_scopes(user)
        if "*" in scopes:
            return True
        if isinstance(target, Expense):
            return target.parts.filter(cost_centre__in=scopes).exists()
        elif isinstance(target, Invoice):
            return target.parts.filter(cost_centre__in=scopes).exists()
        raise TypeError(
            f"Expected an expense or invoice, got {target.__class__.__name__}"
        )

    def accountable_expenses(self, user: User) -> QuerySet:
        from expenses.models import Expense

        scopes = self._get_accounting_scopes(user)
        if "*" in scopes:
            return Expense.objects.all()
        return Expense.objects.filter(expensepart__cost_centre__in=scopes).distinct()

    def accountable_invoices(self, user: User) -> QuerySet:
        from invoices.models import Invoice

        scopes = self._get_accounting_scopes(user)
        if "*" in scopes:
            return Invoice.objects.all()
        return Invoice.objects.filter(invoicepart__cost_centre__in=scopes).distinct()


class SSO(OIDCAuthenticationBackend):

    def get_username(self, claims):
        return claims.get("sub")

    def filter_users_by_claims(self, claims):
        sub = claims.get("sub")
        if not sub:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(username=sub)

    def create_user(self, claims):
        user = super().create_user(claims)
        return self.update_user(user, claims)

    def update_user(self, user, claims):
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.email = claims.get("email", "")
        user.save()
        return user


def get_permissions(user) -> dict[Permission, bool | list[str]]:
    """
    Get permissions for user through the Hive API.

    Result is a dictionary { perm_id => scope[] | True }
    """

    # Jag bryr mig inte om regler och om jag vill lägga saker i en godtycklig dict så gör jag det.

    if "cached_permissions" not in user.__dict__:
        # Fetch permissions from Hive
        response = requests.get(
            settings.HIVE_URL + "/api/v1/user/" + user.username + "/permissions",
            headers={"Authorization": "Bearer " + settings.HIVE_SECRET},
        )
        perms = json.loads(response.content.decode("utf-8"))

        if type(perms) != list:
            raise TypeError(f"Invalid response: {perms}")

        mapping = {}

        for perm in perms:
            perm_id, scope = perm["id"], perm["scope"]

            if scope is None or scope == "*":
                mapping[perm_id] = True
            elif perm_id not in mapping:
                mapping[perm_id] = [scope.lower()]
            elif mapping[perm_id] is not True:
                mapping[perm_id].append(
                    scope.lower()
                )  # else: don't overwrite an existing True (do nothing)

        user.__dict__["cached_permissions"] = mapping

    return user.__dict__["cached_permissions"]


def has_unscoped_permission(perm_id: Permission, user: AbstractBaseUser):
    """
    Check if user has a specific unscoped permission.
    """

    return get_permissions(user).get(perm_id) is True


def has_scoped_permission(perm_id: Permission, scope: str, user: AbstractBaseUser):
    """
    Check if user has a specific scoped permission.
    """

    scopes = get_permissions(user).get(perm_id) or []

    return scopes is True or scope.lower() in scopes


def has_any_permission_scope(perm_id, user):
    """
    Check if user has any scope for a specific permission.
    """

    return perm_id in get_permissions(user)
