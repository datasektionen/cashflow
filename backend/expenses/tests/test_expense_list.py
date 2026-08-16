from rest_framework.test import APIClient

from cashflow.dauth import Permission
from core.factories import UserFactory
from expenses.factories import ExpenseFactory, ExpensePartFactory


class TestExpenseListPermissions:
    def test_unauthenticated_get_returns_403(self):
        response = APIClient().get("/api/expenses/")
        assert response.status_code == 403
        assert response.data["detail"].code == "not_authenticated"

    def test_normal_user_only_receives_own_expenses(self, user, client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        ExpenseFactory.create_batch(20)
        ExpenseFactory.create_batch(5, owner=user.profile)
        response = client.get("/api/expenses/")
        assert response.status_code == 200
        assert response.data["pagination"]["total"] == 5
        assert len(response.data["data"]) == 5
        assert all([e["owner"]["id"] == user.profile.id for e in response.data["data"]])

    def test_user_with_scope_receives_cc_expenses(self, user, client, mocker):
        permissions = {Permission.VIEW_EXPENSES: ["TestCostCenter"]}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )
        ExpenseFactory.create_batch(20)
        cc_expenses = ExpenseFactory.create_batch(2)
        ExpensePartFactory.create_batch(
            2, expense=cc_expenses[0], cost_centre="TestCostCenter"
        )
        ExpensePartFactory.create_batch(
            2, expense=cc_expenses[1], cost_centre="TestCostCenter"
        )

        response = client.get("/api/expenses/")
        assert response.status_code == 200
        assert response.data["pagination"]["total"] == 2
        assert len(response.data["data"]) == 2

    def test_view_all_permission_returns_all_expenses(self, user, client, mocker):
        permissions = {Permission.VIEW_EXPENSES: True}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )

        ExpenseFactory.create_batch(20)
        response = client.get("/api/expenses/")
        assert response.status_code == 200
        assert response.data["pagination"]["total"] == 20
        assert len(response.data["data"]) == 20


class TestExpenseListFilters:
    def test_filter_by_username(self, user, client, mocker):
        permissions = {Permission.VIEW_EXPENSES: True}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )
        ExpenseFactory.create_batch(20)
        target_user = UserFactory()
        ExpenseFactory.create_batch(5, owner=target_user.profile)
        response = client.get("/api/expenses/", {"user": target_user.username})
        assert response.status_code == 200
        assert response.data["pagination"]["total"] == 5
        assert len(response.data["data"]) == 5
        assert all(
            e["owner"]["id"] == target_user.profile.id for e in response.data["data"]
        )

    def test_filter_by_cost_center(self, user, client, mocker):
        permissions = {Permission.VIEW_EXPENSES: True}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )
        ExpenseFactory.create_batch(20)
        target_cc = "TestCostCenter"
        expenses = ExpenseFactory.create_batch(5)
        for expense in expenses:
            ExpensePartFactory.create_batch(2, expense=expense, cost_centre=target_cc)

        response = client.get("/api/expenses/", {"cost_centre": target_cc})

        assert response.status_code == 200
        assert response.data["pagination"]["total"] == 5
        assert len(response.data["data"]) == 5


class TestExpenseListSorting:
    def test_defaults_to_created_at_desc(self, user, client, mocker):
        permissions = {Permission.VIEW_EXPENSES: True}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )
        first = ExpenseFactory()
        second = ExpenseFactory()

        response = client.get("/api/expenses/")

        assert response.status_code == 200
        ids = [e["id"] for e in response.data["data"]]
        assert ids.index(second.id) < ids.index(first.id)

    def test_sorting_by_date_asc(self, user, client, mocker):
        permissions = {Permission.VIEW_EXPENSES: True}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )
        earlier = ExpenseFactory(expense_date="2024-01-01")
        later = ExpenseFactory(expense_date="2024-06-01")

        response = client.get("/api/expenses/", {"sorting": "date"})

        assert response.status_code == 200
        ids = [e["id"] for e in response.data["data"]]
        assert ids.index(earlier.id) < ids.index(later.id)

    def test_sorting_by_date_desc(self, user, client, mocker):
        permissions = {Permission.VIEW_EXPENSES: True}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )
        earlier = ExpenseFactory(expense_date="2024-01-01")
        later = ExpenseFactory(expense_date="2024-06-01")

        response = client.get("/api/expenses/", {"sorting": "-date"})

        assert response.status_code == 200
        ids = [e["id"] for e in response.data["data"]]
        assert ids.index(later.id) < ids.index(earlier.id)

    def _expense_with_total(self, amount: str):
        # ExpenseFactory auto-creates one part with a random amount, so clear it
        # and set a known amount to make the total deterministic.
        expense = ExpenseFactory.create()
        expense.parts.all().delete()
        ExpensePartFactory(expense=expense, amount=amount)
        return expense

    def test_sorting_by_total_desc(self, user, client, mocker):
        permissions = {Permission.VIEW_EXPENSES: True}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )
        cheap = self._expense_with_total("10.00")
        pricey = self._expense_with_total("100.00")

        response = client.get("/api/expenses/", {"sorting": "-total"})

        assert response.status_code == 200
        ids = [e["id"] for e in response.data["data"]]
        assert ids.index(pricey.id) < ids.index(cheap.id)
        totals = {e["id"]: e["total"] for e in response.data["data"]}
        assert totals[cheap.id] == "10.00"
        assert totals[pricey.id] == "100.00"

    def test_sorting_by_total_asc(self, user, client, mocker):
        permissions = {Permission.VIEW_EXPENSES: True}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )
        cheap = self._expense_with_total("10.00")
        pricey = self._expense_with_total("100.00")

        response = client.get("/api/expenses/", {"sorting": "total"})

        assert response.status_code == 200
        ids = [e["id"] for e in response.data["data"]]
        assert ids.index(cheap.id) < ids.index(pricey.id)
