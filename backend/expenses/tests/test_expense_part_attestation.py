import pytest
from rest_framework.test import APIClient

from cashflow.dauth import Permission
from core.factories import UserFactory
from expenses.factories import ExpensePartFactory
from expenses.models import Comment


class TestExpensePartAttestation:

    @pytest.mark.django_db
    def test_correct_attestation(self, today, mocker):
        user = UserFactory.create()
        client = APIClient()
        client.force_authenticate(user=user)
        expense_part = ExpensePartFactory.create()
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={
                Permission.ATTEST: [expense_part.cost_centre],
                Permission.VIEW_EXPENSES: [expense_part.cost_centre],
            },
        )

        response = client.post(f"/api/expense-parts/{expense_part.id}/attest/")

        assert response.status_code == 204
        expense_part.refresh_from_db()
        assert expense_part.attest_date == today
        assert expense_part.attested_by == user.profile

        comment = Comment.objects.filter(
            expense=expense_part.expense, author=user.profile
        )
        assert comment.exists()

    def test_rejects_unauthorized(self, user, client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        expense_part = ExpensePartFactory.create(expense__owner=user.profile)
        response = client.post(
            f"/api/expense-parts/{expense_part.id}/attest/",
        )
        assert response.status_code == 403
        assert response.data["detail"].code == "attestation_permission_denied"

    def test_user_cant_attest_own_expense(self, user, client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.ATTEST: ["A"]},
            autospec=True,
        )
        expense_part = ExpensePartFactory.create(
            cost_centre="A", expense__owner=user.profile
        )
        response = client.post(
            f"/api/expense-parts/{expense_part.id}/attest/",
        )
        assert response.status_code == 403
        assert response.data["detail"].code == "attestation_permission_denied"

    @pytest.mark.django_db
    def test_cant_attest_flagged_expense(self, user, client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.ATTEST: ["A"], Permission.VIEW_EXPENSES: ["A"]},
            autospec=True,
        )
        expense_part = ExpensePartFactory.create(
            cost_centre="A", expense__is_flagged=True
        )
        response = client.post(
            f"/api/expense-parts/{expense_part.id}/attest/",
        )
        assert response.status_code == 409
        assert response.data["detail"].code == "resource_is_flagged"
