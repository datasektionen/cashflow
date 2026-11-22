from cashflow.dauth import Permission
from expenses.factories import ExpenseFactory, PaymentFactory
from core.models import Claim


class TestExpenseDelete:
    def test_owner_can_delete_own_unreimbursed_expense(self, client, expense, mocker):
        # `expense` is owned by the authenticated `user` fixture.
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)

        response = client.delete(f"/api/expenses/{expense.data_id}/")

        assert response.status_code == 204
        assert not Claim.objects.filter(id=expense.id).exists()

    def test_rejects_own_reimbursed_expense(self, client, expense, mocker):
        expense.expense_data.reimbursement = PaymentFactory()
        expense.expense_data.save()
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)

        response = client.delete(f"/api/expenses/{expense.data_id}/")

        assert response.status_code == 403
        assert response.data["detail"].code == "deletion_permission_denied"
        assert Claim.objects.filter(id=expense.id).exists()

    def test_rejects_other_users_expense_without_permission(self, client, mocker):
        other_expense = ExpenseFactory()
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={"view-all": True},
            autospec=True,
        )

        response = client.delete(f"/api/expenses/{other_expense.data_id}/")

        assert response.status_code == 403
        assert response.data["detail"].code == "deletion_permission_denied"
        assert Claim.objects.filter(id=other_expense.id).exists()

    def test_deletes_other_users_expense_with_permission(self, client, mocker):
        other_expense = ExpenseFactory()
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.DELETE: True, "view-all": True},
            autospec=True,
        )

        response = client.delete(f"/api/expenses/{other_expense.data_id}/")

        assert response.status_code == 204
        assert not Claim.objects.filter(id=other_expense.id).exists()

    def test_rejects_reimbursed_expense_with_permission(self, client, mocker):
        other_expense = ExpenseFactory()
        other_expense.expense_data.reimbursement = PaymentFactory()
        other_expense.expense_data.save()
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.DELETE: True, "view-all": True},
            autospec=True,
        )

        response = client.delete(f"/api/expenses/{other_expense.data_id}/")

        assert response.status_code == 403
        assert response.data["detail"].code == "deletion_permission_denied"
        assert Claim.objects.filter(id=other_expense.id).exists()
