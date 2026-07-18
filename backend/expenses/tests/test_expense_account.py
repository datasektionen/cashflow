from cashflow.dauth import Permission
from expenses.models import Comment


class TestExpenseAccount:
    def test_rejects_unauthorized(self, user, client, expense, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        response = client.post(
            f"/api/expenses/{expense.id}/account/",
            {"voucher_number": "A123"},
            format="json",
        )
        assert response.status_code == 403
        assert response.data["detail"].code == "accounting_permission_denied"

    def test_manual_voucher_number_accounts(self, user, client, expense, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.ACCOUNTING: True},
            autospec=True,
        )
        response = client.post(
            f"/api/expenses/{expense.id}/account/",
            {"voucher_number": "A123"},
            format="json",
        )
        assert response.status_code == 200, response.json()
        expense.refresh_from_db()
        assert expense.verification == "A123"
        assert Comment.objects.filter(expense=expense, author=user.profile).exists()

    def test_rejects_already_accounted(self, user, client, expense, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.ACCOUNTING: True},
            autospec=True,
        )
        expense.verification = "A1"
        expense.save()
        response = client.post(
            f"/api/expenses/{expense.id}/account/",
            {"voucher_number": "A123"},
            format="json",
        )
        assert response.status_code == 409
        assert response.data["detail"].code == "already_accounted"

    def test_voucher_rows_without_service_returns_503(
        self, user, client, expense, mocker
    ):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.ACCOUNTING: True},
            autospec=True,
        )
        response = client.post(
            f"/api/expenses/{expense.id}/account/",
            {"voucher_rows": [{"account": 1930, "cost_centre": 100, "debit": "50.00"}]},
            format="json",
        )
        assert response.status_code == 503
        assert response.data["detail"].code == "fortnox_service_not_available"
