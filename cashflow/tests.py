from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from pytest import fixture

from cashflow.dauth import HiveAccountingPermissions, Permission
from cashflow.utils import may_authenticate_fortnox
from expenses.factories import ExpenseFactory, ExpensePartFactory
from invoices.factories import InvoiceFactory, InvoicePartFactory

UserModel = get_user_model()


@fixture
def user(db):
    return UserModel.objects.create_user(username="testuser")


def test_normal_user_cant_authenticate_fortnox(user):
    with patch("cashflow.dauth.get_permissions", return_value={}):
        assert not may_authenticate_fortnox(user)


def test_permitted_user_may_authenticate_fortnox(user):
    with patch("cashflow.dauth.get_permissions", return_value={"manage-fortnox": True}):
        assert may_authenticate_fortnox(user)


def test_auth_endpoint_forbidden_without_permission(db, user):
    client = Client()
    client.force_login(user)
    with (
        patch("cashflow.utils.has_accounting_permissions", return_value=False),
        patch("cashflow.utils.may_authenticate_fortnox", return_value=False),
    ):
        response = client.get(reverse("fortnox-auth-get"))
    assert response.status_code == 403


def test_auth_endpoint_accessible_with_permission(db, user):
    client = Client()
    client.force_login(user)
    with (
        patch("cashflow.utils.has_accounting_permissions", return_value=False),
        patch("cashflow.utils.may_authenticate_fortnox", return_value=True),
    ):
        response = client.get(reverse("fortnox-auth-get"))
    assert response.status_code != 403


@fixture
def expense(db):
    return ExpenseFactory()


@fixture
def expense_set(db):
    return ExpenseFactory.create_batch(20)


@fixture
def invoice_set(db):
    return InvoiceFactory.create_batch(20)


@fixture
def provider():
    return HiveAccountingPermissions()


class TestHiveAccountingPermissions:
    def test_user_with_no_scopes_may_not_account(user, provider, expense_set, mocker):
        mocker.patch("cashflow.dauth.get_permissions", autospec=True, return_value={})
        assert provider.accountable_expenses(user).count() == 0
        for e in expense_set:
            assert provider.may_account(e, user) == False

    def test_user_with_wildcard_scope_may_account_all_expenses(
        self, provider, user, expense_set, mocker
    ):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            autospec=True,
            return_value={Permission.ACCOUNTING: "*"},
        )

        assert provider.accountable_expenses(user).count() == 20
        for e in expense_set:
            assert provider.may_account(e, user) == True

    def test_user_with_scope_may_account_expenses(
        self, provider, user, expense_set, mocker
    ):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            autospec=True,
            return_value={Permission.ACCOUNTING: ["Test"]},
        )
        cc_expenses = ExpenseFactory.create_batch(5)
        for e in cc_expenses:
            ExpensePartFactory.create(expense=e, cost_centre="Test")

        assert provider.accountable_expenses(user).count() == 5
        for e in cc_expenses:
            assert provider.may_account(e, user) == True

    def test_user_with_no_scopes_may_not_account_invoices(
        self, provider, user, invoice_set, mocker
    ):
        mocker.patch("cashflow.dauth.get_permissions", autospec=True, return_value={})
        assert provider.accountable_invoices(user).count() == 0
        for i in invoice_set:
            assert provider.may_account(i, user) == False

    def test_user_with_wildcard_scope_may_account_all_invoices(
        self, provider, user, invoice_set, mocker
    ):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            autospec=True,
            return_value={Permission.ACCOUNTING: "*"},
        )

        assert provider.accountable_invoices(user).count() == 20
        for i in invoice_set:
            assert provider.may_account(i, user) == True

    def test_user_with_scope_may_account_invoices(
        self, provider, user, invoice_set, mocker
    ):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            autospec=True,
            return_value={Permission.ACCOUNTING: ["Test"]},
        )
        cc_invoices = InvoiceFactory.create_batch(5)
        for i in cc_invoices:
            InvoicePartFactory.create(invoice=i, cost_centre="Test")

        assert provider.accountable_invoices(user).count() == 5
        for i in cc_invoices:
            assert provider.may_account(i, user) == True
