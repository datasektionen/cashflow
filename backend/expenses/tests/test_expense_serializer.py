import pytest
from hypothesis import given, settings, HealthCheck, strategies as st

from expenses.api.serializers import ExpenseSerializer
from expenses.factories import PaymentFactory


class TestExpenseSerializer:

    @pytest.mark.django_db
    def test_unpaid_expense_serializes_null_payment_and_flags(self, expense):
        data = ExpenseSerializer(expense).data
        assert data["payment"] is None
        assert data["confirmed_by"] is None
        assert data["is_flagged"] is None

    @pytest.mark.django_db
    def test_paid_expense_serializes_payment(self, expense):
        payment = PaymentFactory(receiver=expense.owner)
        expense.reimbursement = payment
        expense.save()
        data = ExpenseSerializer(expense).data
        assert data["payment"]["id"] == payment.id
        assert data["payment"]["receiver"]["id"] == expense.owner.id

    @pytest.mark.django_db
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(st.from_regex(r"[A-Z]\d+", fullmatch=True))
    def test_accepts_valid_verification(self, expense, verification):
        expense.verification = verification
        serializer = ExpenseSerializer(expense)
        assert serializer.data["verification"] == verification

    @given((st.from_regex(r"[a-z]\d+", fullmatch=True)))
    def test_rejects_lowercase_verification(self, verification):
        serializer = ExpenseSerializer(data={"verification": verification})
        assert not serializer.is_valid()
        assert "verification" in serializer.errors

    @pytest.mark.django_db
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(st.from_regex(r"[ \t\n]*[A-Z]\d+[ \t\n]*", fullmatch=True))
    def test_strips_whitespace_in_verification(self, expense, verification):
        expense.verification = verification.strip()
        serializer = ExpenseSerializer(expense)
        assert serializer.data["verification"] == verification.strip()
        assert not any(c.isspace() for c in serializer.data["verification"])
