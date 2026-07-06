import json
from enum import Enum

import requests
from django.conf import settings
from django.contrib.auth.models import User, AbstractBaseUser
from django.db.models import QuerySet
from pydantic import BaseModel

from mozilla_django_oidc.auth import OIDCAuthenticationBackend

import core.permissions


class Permission(str, Enum):
    ACCOUNTING = "accounting"
    ATTEST = "attest"
    CONFIRM = "confirm"
    DELETE = "delete"
    EDIT_INVOICE = "edit-invoice"
    MANAGE_FORTNOX = "manage-fortnox"
    MODERATE_COMMENTS = "moderate-comments"
    PAY = "pay"
    UNATTEST = "unattest"
    UNCONFIRM = "unconfirm"
    VIEW_ALL_PAYMENTS = "view-all-payments"
    VIEW_EXPENSES = "view-expenses"


class HivePermission(BaseModel):
    id: Permission
    scope: bool | list[str]


class Hive(core.permissions.PermissionProvider):

    def _scopes(
        self, user: AbstractBaseUser, perm: Permission | str
    ) -> list[str] | bool:
        return get_permissions(user).get(perm, [])  # type: ignore[arg-type]

    def _has_unscoped(self, user: AbstractBaseUser, perm: Permission | str) -> bool:
        return get_permissions(user).get(perm) is True  # type: ignore[arg-type]

    def _has_scoped(
        self, user: AbstractBaseUser, perm: Permission | str, cost_centre: str
    ) -> bool:
        scopes = get_permissions(user).get(perm)  # type: ignore[arg-type]
        if scopes is True:
            return True
        return isinstance(scopes, list) and cost_centre.lower() in scopes

    def _has_any_scope(self, user: AbstractBaseUser, perm: Permission | str) -> bool:
        return perm in get_permissions(user)  # type: ignore[arg-type]

    def may_view_all(self, user: AbstractBaseUser) -> bool:
        return self._has_unscoped(user, "view-all") or self._has_scoped(
            user, Permission.VIEW_EXPENSES, "*"
        )

    def may_view_all_payments(self, user: AbstractBaseUser) -> bool:
        return self._has_unscoped(user, Permission.VIEW_ALL_PAYMENTS)

    def viewable_cost_centres(self, user: AbstractBaseUser) -> list[str]:
        scopes = get_permissions(user).get(Permission.VIEW_EXPENSES, [])
        return scopes if isinstance(scopes, list) else []

    def may_attest(self, user: AbstractBaseUser, cost_centre: str) -> bool:
        return self._has_scoped(user, Permission.ATTEST, cost_centre)

    def may_attest_some(self, user: AbstractBaseUser) -> bool:
        return self._has_any_scope(user, Permission.ATTEST)

    def attestable_cost_centres(self, user: AbstractBaseUser) -> list[str]:
        from expenses.models import ExpensePart
        from invoices.models import InvoicePart

        all_ccs = set(ExpensePart.objects.values_list("cost_centre", flat=True)) | set(
            InvoicePart.objects.values_list("cost_centre", flat=True)
        )

        if get_permissions(user).get(Permission.ATTEST) is True:
            return list(all_ccs)
        return [cc for cc in all_ccs if self.may_attest(user, cc)]

    def may_unattest(self, user: AbstractBaseUser) -> bool:
        return self._has_unscoped(user, Permission.UNATTEST)

    def may_confirm(self, user: AbstractBaseUser) -> bool:
        return self._has_unscoped(user, Permission.CONFIRM)

    def may_account(self, user: AbstractBaseUser, target) -> bool:
        from expenses.models import Expense
        from invoices.models import Invoice

        scopes = get_permissions(user).get(Permission.ACCOUNTING, [])
        if scopes is True or "*" in scopes:
            return True
        if isinstance(target, Expense):
            return target.parts.filter(cost_centre__in=scopes).exists()
        if isinstance(target, Invoice):
            return target.parts.filter(cost_centre__in=scopes).exists()
        raise TypeError(
            f"Expected an expense or invoice, got {target.__class__.__name__}"
        )

    def may_account_some(self, user: AbstractBaseUser) -> bool:
        return self._has_any_scope(user, Permission.ACCOUNTING)

    def may_account_cost_centre(self, user: AbstractBaseUser, cost_centre: str) -> bool:
        return self._has_scoped(user, Permission.ACCOUNTING, cost_centre)

    def accountable_cost_centres(self, user: AbstractBaseUser) -> list[str]:
        from expenses.models import ExpensePart
        from invoices.models import InvoicePart

        all_ccs = set(ExpensePart.objects.values_list("cost_centre", flat=True)) | set(
            InvoicePart.objects.values_list("cost_centre", flat=True)
        )

        if get_permissions(user).get(Permission.ACCOUNTING) is True:
            return list(all_ccs)
        return [cc for cc in all_ccs if self.may_account_cost_centre(user, cc)]

    def accountable_expenses(self, user: AbstractBaseUser) -> QuerySet:
        from expenses.models import Expense

        scopes = get_permissions(user).get(Permission.ACCOUNTING, [])
        if scopes is True or "*" in scopes:
            return Expense.objects.all()
        return Expense.objects.filter(expensepart__cost_centre__in=scopes).distinct()

    def accountable_invoices(self, user: AbstractBaseUser) -> QuerySet:
        from invoices.models import Invoice

        scopes = get_permissions(user).get(Permission.ACCOUNTING, [])
        if scopes is True or "*" in scopes:
            return Invoice.objects.all()
        return Invoice.objects.filter(invoicepart__cost_centre__in=scopes).distinct()

    def may_pay(self, user: AbstractBaseUser) -> bool:
        return self._has_unscoped(user, Permission.PAY)

    def may_delete(self, user: AbstractBaseUser) -> bool:
        return self._has_unscoped(user, Permission.DELETE)

    def may_edit_invoice(self, user: AbstractBaseUser) -> bool:
        return self._has_unscoped(user, Permission.EDIT_INVOICE)

    def may_moderate_comments(self, user: AbstractBaseUser) -> bool:
        return self._has_unscoped(user, Permission.MODERATE_COMMENTS)

    def may_firmatecknare(self, user: AbstractBaseUser) -> bool:
        return "attest-firmatecknare" in get_permissions(user)

    def may_view_account(self, user: AbstractBaseUser) -> bool:
        return "view-account" in get_permissions(user)


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
