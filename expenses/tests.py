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
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.test import APIClient

from cashflow.dauth import Permission
from core.factories import UserFactory
from expenses.factories import ExpenseFactory, ExpensePartFactory
from expenses.models import Profile


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
        response = APIClient().get("/api/claims/")
        assert response.status_code == 403
        assert response.data["detail"].code == "not_authenticated"

    def test_normal_user_only_receives_own_expenses(self, user, client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        ExpenseFactory.create_batch(20)
        ExpenseFactory.create_batch(5, owner=user.profile)
        response = client.get("/api/claims/")
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

        response = client.get("/api/claims/")
        assert response.status_code == 200
        assert response.data["pagination"]["total"] == 2
        assert len(response.data["data"]) == 2

    def test_view_all_permission_returns_all_expenses(self, user, client, mocker):
        permissions = {Permission.VIEW_EXPENSES: "*"}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )

        ExpenseFactory.create_batch(20)
        response = client.get("/api/claims/")
        assert response.status_code == 200
        assert response.data["pagination"]["total"] == 20
        assert len(response.data["data"]) == 20


class TestExpenseListFilters:
    def test_filter_by_username(self, user, client, mocker):
        permissions = {Permission.VIEW_EXPENSES: "*"}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )
        ExpenseFactory.create_batch(20)
        target_user = UserFactory()
        ExpenseFactory.create_batch(5, owner=target_user.profile)
        response = client.get("/api/claims/", {"user": target_user.username})
        assert response.status_code == 200
        assert response.data["pagination"]["total"] == 5
        assert len(response.data["data"]) == 5
        assert all(
            e["owner"]["id"] == target_user.profile.id for e in response.data["data"]
        )

    def test_filter_by_cost_center(self, user, client, mocker):
        permissions = {Permission.VIEW_EXPENSES: "*"}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )
        ExpenseFactory.create_batch(20)
        target_cc = "TestCostCenter"
        expenses = ExpenseFactory.create_batch(5)
        for expense in expenses:
            ExpensePartFactory.create_batch(2, expense=expense, cost_centre=target_cc)

        response = client.get("/api/claims/", {"cost_center": target_cc})

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
            "/api/claims/",
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
            "/api/claims/",
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
            "/api/claims/",
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
            "/api/claims/",
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
            "/api/claims/",
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
