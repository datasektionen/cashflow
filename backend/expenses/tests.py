# Create your tests here.
# This is an economy system. Of course we cannot test an
# economy system, that would be considered smart.
#
# But we keep this file. It both looks good and makes things
# less complicated when we get serious.
#
# Better late than never
import json
import pytest
from django.conf import settings as django_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.serializers.json import DjangoJSONEncoder
from hypothesis import given, settings, HealthCheck, strategies as st
from rest_framework.test import APIClient

from cashflow.dauth import Permission
from core.factories import UserFactory
from expenses.api.serializers import ExpenseSerializer
from expenses.factories import ExpenseFactory, ExpensePartFactory, PaymentFactory
from expenses.models import Profile, Comment


@pytest.fixture
def client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def expense(user):
    return ExpenseFactory(owner=user.profile)


class TestProfileSignal:
    # As of now, profiles should be automatically created using a signal
    # when a user is created.
    # This test might be useful if this changes
    def test_profile_exists_after_new_user(self, db):
        user = UserFactory()
        assert Profile.objects.filter(user=user).exists()


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


class TestExpenseCreate:
    def test_accepts_files(self, user, client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        file = SimpleUploadedFile("receipt.jpg", b"content", content_type="image/jpeg")
        file2 = SimpleUploadedFile(
            "receipt2.jpg", b"content", content_type="image/jpeg"
        )

        part = {
            "cost_centre": "A",
            "secondary_cost_centre": "B",
            "budget_line": "C",
            "amount": "100.00",
        }

        response = client.post(
            "/api/expenses/",
            {
                "description": "Test expense",
                "files": [file, file2],
                "expense_date": "2026-01-01",
                "parts": json.dumps([part], cls=DjangoJSONEncoder),
            },
            format="multipart",
        )

        assert response.status_code == 201, response.json()

    def test_cant_set_other_owner(self, user, client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        target_user = UserFactory()
        file = SimpleUploadedFile("receipt.jpg", b"content", content_type="image/jpeg")

        part = {
            "cost_centre": "A",
            "secondary_cost_centre": "B",
            "budget_line": "C",
            "amount": "100.00",
        }

        response = client.post(
            "/api/expenses/",
            {
                "description": "Test expense",
                "expense_date": "2026-01-01",
                "owner": target_user.profile.id,  # not allowed
                "files": [file],
                "parts": json.dumps([part], cls=DjangoJSONEncoder),
            },
            format="multipart",
        )

        assert response.status_code == 201
        assert response.data["owner"]["id"] == user.profile.id

    def test_must_contain_file(self, user, client):
        response = client.post(
            "/api/expenses/",
            {
                "description": "Test expense",
                "expense_date": "2026-01-01",
            },
        )
        assert response.status_code == 400
        assert response.data["detail"].code == "file_required"

    def test_must_contain_part(self, user, client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        file = SimpleUploadedFile("receipt.jpg", b"content", content_type="image/jpeg")
        response = client.post(
            "/api/expenses/",
            {
                "description": "Test expense",
                "expense_date": "2026-01-01",
                "files": [file],
            },
        )
        assert response.status_code == 400
        assert response.data["parts"][0].code == "required"

    def test_rejects_invalid_parts_json(self, user, client):
        file = SimpleUploadedFile("receipt.jpg", b"content", content_type="image/jpeg")
        response = client.post(
            "/api/expenses/",
            {
                "description": "Test expense",
                "expense_date": "2026-01-01",
                "files": [file],
                "parts": "not valid json{",
            },
            format="multipart",
        )
        assert response.status_code == 400
        assert response.data["detail"].code == "part_invalid_json"


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
