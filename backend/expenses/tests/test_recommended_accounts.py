from django.conf import settings as django_settings
from rest_framework.test import APIClient

from cashflow.dauth import Permission
from expenses.factories import ExpenseFactory, ExpensePartFactory


class TestRecommendedAccounts:
    def test_populated_on_retrieve(self, user, client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.VIEW_EXPENSES: True},
            autospec=True,
        )
        mocker.patch(
            "cashflow.api.serializers.retrieve_account_from_gordian",
            return_value=[4010, 4011],
            autospec=True,
        )
        expense = ExpenseFactory(owner=user.profile)
        ExpensePartFactory.create(expense=expense)

        response = client.get(f"/api/expenses/{expense.id}/")
        assert response.status_code == 200
        assert response.data["parts"][0]["recommended_accounts"] == [4010, 4011]
        assert (
            response.data["recommended_credit_account"]
            == django_settings.FORTNOX_EXPENSE_CREDIT_ACCOUNT
        )

    def test_null_on_list(self, user, client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.VIEW_EXPENSES: True},
            autospec=True,
        )
        gordian = mocker.patch(
            "cashflow.api.serializers.retrieve_account_from_gordian",
            autospec=True,
        )
        expense = ExpenseFactory(owner=user.profile)
        ExpensePartFactory.create(expense=expense)

        response = client.get("/api/expenses/")
        assert response.status_code == 200
        assert response.data["data"][0]["parts"][0]["recommended_accounts"] is None
        assert response.data["data"][0]["recommended_credit_account"] is None
        # No GOrdian lookup should happen for list responses.
        gordian.assert_not_called()

    def test_empty_when_budget_line_unresolved(self, user, client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.VIEW_EXPENSES: True},
            autospec=True,
        )
        mocker.patch(
            "cashflow.api.serializers.retrieve_account_from_gordian",
            side_effect=ValueError("no such budget line"),
            autospec=True,
        )
        expense = ExpenseFactory(owner=user.profile)
        ExpensePartFactory.create(expense=expense)

        response = client.get(f"/api/expenses/{expense.id}/")
        assert response.status_code == 200
        assert response.data["parts"][0]["recommended_accounts"] == []

    def test_cost_centre_populated_on_retrieve(self, user, mocker):
        # ACCOUNTING permission makes FortnoxServiceMiddleware attach
        # request.fortnox_service, which the recommendation requires. The
        # middleware runs before DRF authentication, so session login is
        # needed (force_authenticate would leave request.user anonymous
        # during the middleware phase).
        client = APIClient()
        client.force_login(user)
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={
                Permission.VIEW_EXPENSES: True,
                Permission.ACCOUNTING: True,
            },
            autospec=True,
        )
        mocker.patch(
            "cashflow.api.serializers.retrieve_account_from_gordian",
            return_value=[4010],
            autospec=True,
        )
        fortnox_cc = mocker.patch(
            "cashflow.utils.fortnox_cost_center_for_part", autospec=True
        )
        fortnox_cc.return_value.Code = "123"
        expense = ExpenseFactory(owner=user.profile)
        ExpensePartFactory.create(expense=expense)

        response = client.get(f"/api/expenses/{expense.id}/")
        assert response.status_code == 200
        assert response.data["parts"][0]["recommended_cost_centre"] == "123"

    def test_cost_centre_null_without_fortnox_service(self, user, client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.VIEW_EXPENSES: True},
            autospec=True,
        )
        mocker.patch(
            "cashflow.api.serializers.retrieve_account_from_gordian",
            return_value=[4010],
            autospec=True,
        )
        expense = ExpenseFactory(owner=user.profile)
        ExpensePartFactory.create(expense=expense)

        response = client.get(f"/api/expenses/{expense.id}/")
        assert response.status_code == 200
        assert response.data["parts"][0]["recommended_cost_centre"] is None
