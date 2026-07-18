import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.serializers.json import DjangoJSONEncoder

from core.factories import UserFactory


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
