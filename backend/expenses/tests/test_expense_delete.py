from cashflow.dauth import Permission
from expenses.factories import ExpenseFactory, PaymentFactory
from expenses.models import Expense


class TestExpenseDelete:
    def test_owner_can_delete_own_unreimbursed_expense(self, client, expense, mocker):
        # `expense` is owned by the authenticated `user` fixture.
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)

        response = client.delete(f"/api/expenses/{expense.id}/")

        assert response.status_code == 204
        assert not Expense.objects.filter(id=expense.id).exists()

    def test_rejects_own_reimbursed_expense(self, client, expense, mocker):
        expense.reimbursement = PaymentFactory()
        expense.save()
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)

        response = client.delete(f"/api/expenses/{expense.id}/")

        assert response.status_code == 403
        assert response.data["detail"].code == "deletion_permission_denied"
        assert Expense.objects.filter(id=expense.id).exists()

    def test_rejects_other_users_expense_without_permission(self, client, mocker):
        other_expense = ExpenseFactory()
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={"view-all": True},
            autospec=True,
        )

        response = client.delete(f"/api/expenses/{other_expense.id}/")

        assert response.status_code == 403
        assert response.data["detail"].code == "deletion_permission_denied"
        assert Expense.objects.filter(id=other_expense.id).exists()

    def test_deletes_other_users_expense_with_permission(self, client, mocker):
        other_expense = ExpenseFactory()
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.DELETE: True, "view-all": True},
            autospec=True,
        )

        response = client.delete(f"/api/expenses/{other_expense.id}/")

        assert response.status_code == 204
        assert not Expense.objects.filter(id=other_expense.id).exists()

    def test_rejects_reimbursed_expense_with_permission(self, client, mocker):
        other_expense = ExpenseFactory()
        other_expense.reimbursement = PaymentFactory()
        other_expense.save()
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.DELETE: True, "view-all": True},
            autospec=True,
        )

        response = client.delete(f"/api/expenses/{other_expense.id}/")

        assert response.status_code == 403
        assert response.data["detail"].code == "deletion_permission_denied"
        assert Expense.objects.filter(id=other_expense.id).exists()
