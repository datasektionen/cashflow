from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from pytest import fixture

from cashflow.dauth import Hive, Permission
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
    return Hive()


class TestHiveAccountingPermissions:
    def test_user_with_no_scopes_may_not_account(user, provider, expense_set, mocker):
        mocker.patch("cashflow.dauth.get_permissions", autospec=True, return_value={})
        assert provider.accountable_expenses(user).count() == 0
        for e in expense_set:
            assert provider.may_account(user, e) == False

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
            assert provider.may_account(user, e) == True

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
            assert provider.may_account(user, e) == True

    def test_user_with_no_scopes_may_not_account_invoices(
        self, provider, user, invoice_set, mocker
    ):
        mocker.patch("cashflow.dauth.get_permissions", autospec=True, return_value={})
        assert provider.accountable_invoices(user).count() == 0
        for i in invoice_set:
            assert provider.may_account(user, i) == False

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
            assert provider.may_account(user, i) == True

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
            assert provider.may_account(user, i) == True

    def test_scope_matches_cost_centre_case_insensitively(self, provider, user, mocker):
        # Hive preserves scope case; get_permissions lowercases it, while the
        # stored cost centre keeps its original case. Matching must therefore be
        # case-insensitive (regression: a mixed-case cost centre was rejected
        # even though the user held the scope).
        mocker.patch(
            "cashflow.dauth.get_permissions",
            autospec=True,
            return_value={Permission.ACCOUNTING: ["mottagningen 2026"]},
        )
        cc_expenses = ExpenseFactory.create_batch(3)
        for e in cc_expenses:
            ExpensePartFactory.create(expense=e, cost_centre="Mottagningen 2026")
        cc_invoices = InvoiceFactory.create_batch(2)
        for i in cc_invoices:
            InvoicePartFactory.create(invoice=i, cost_centre="Mottagningen 2026")

        assert provider.accountable_expenses(user).count() == 3
        assert provider.accountable_invoices(user).count() == 2
        for e in cc_expenses:
            assert provider.may_account(user, e) == True
        for i in cc_invoices:
            assert provider.may_account(user, i) == True


class TestHiveViewExpensesPermissions:
    def test_scoped_view_matches_cost_centre_case_insensitively(
        self, provider, user, mocker
    ):
        # Same casing pitfall as accounting: scope comes back lowercased while the
        # stored cost centre keeps its case. viewable_cost_centres must return the
        # original-case name so the case-sensitive `cost_centre__in` filter matches.
        from expenses.models import Expense

        mocker.patch(
            "cashflow.dauth.get_permissions",
            autospec=True,
            return_value={Permission.VIEW_EXPENSES: ["mottagningen 2026"]},
        )
        cc_expenses = ExpenseFactory.create_batch(3)
        for e in cc_expenses:
            ExpensePartFactory.create(expense=e, cost_centre="Mottagningen 2026")

        assert provider.viewable_cost_centres(user) == ["Mottagningen 2026"]
        viewable_ids = set(
            Expense.objects.viewable_by(user).values_list("id", flat=True)
        )
        assert {e.id for e in cc_expenses} <= viewable_ids

    def test_accounting_scope_grants_visibility(self, provider, user, mocker):
        # Accounting permission alone (no view-expenses) must make the expense
        # visible, so it shows up in the account queue (viewable_by ∩ accountable).
        from expenses.models import Expense

        mocker.patch(
            "cashflow.dauth.get_permissions",
            autospec=True,
            return_value={Permission.ACCOUNTING: ["mottagningen 2026"]},
        )
        e = ExpenseFactory.create()
        ExpensePartFactory.create(expense=e, cost_centre="Mottagningen 2026")

        viewable = set(Expense.objects.viewable_by(user).values_list("id", flat=True))
        assert e.id in viewable

    def test_attest_scope_grants_visibility(self, provider, user, mocker):
        from expenses.models import Expense

        mocker.patch(
            "cashflow.dauth.get_permissions",
            autospec=True,
            return_value={Permission.ATTEST: ["mottagningen 2026"]},
        )
        e = ExpenseFactory.create()
        ExpensePartFactory.create(expense=e, cost_centre="Mottagningen 2026")

        viewable = set(Expense.objects.viewable_by(user).values_list("id", flat=True))
        assert e.id in viewable

    def test_confirm_permission_grants_full_visibility(
        self, provider, user, expense_set, mocker
    ):
        # confirm is unscoped, so a confirmer may view every expense.
        from expenses.models import Expense

        mocker.patch(
            "cashflow.dauth.get_permissions",
            autospec=True,
            return_value={Permission.CONFIRM: True},
        )
        assert Expense.objects.viewable_by(user).count() == Expense.objects.count() > 0


class TestGordianParsing:

    def test_known_cost_centre_type_kept(self):
        from cashflow.gordian import GCostCenter

        cc = GCostCenter.model_validate(
            {
                "CostCentreID": 1,
                "CostCentreName": "Testnämnden",
                "CostCentreType": "committee",
            }
        )
        assert cc.type == "committee"


class TestCostCentreListActiveFilter:
    def test_active_filter_excludes_inactive_cost_centres(self, db, user):
        from cashflow.gordian import GCostCenter

        e = ExpenseFactory()
        ExpensePartFactory.create(expense=e, cost_centre="Retired CC")

        client = Client()
        client.force_login(user)
        with (
            patch("cashflow.dauth.get_permissions", return_value={}),
            patch(
                "cashflow.api.views.list_cost_centres_from_gordian",
                return_value=[
                    GCostCenter(
                        CostCentreID=1,
                        CostCentreName="Active CC",
                        CostCentreType="committee",
                    )
                ],
            ),
        ):
            response = client.get(reverse("costcentre-list"), {"active": "true"})

        names = {cc["name"] for cc in response.json()["data"]}
        assert names == {"Active CC"}
