import datetime
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from cashflow.dauth import Permission
from ..factories import InvoiceFactory

YESTERDAY = datetime.datetime.now() - datetime.timedelta(days=1)
TODAY = datetime.date.today()
TOMORROW = datetime.date.today() + datetime.timedelta(days=1)


PART = {
    "cost_centre": "A",
    "secondary_cost_centre": "B",
    "budget_line": "C",
    "amount": "100.00",
}


def make_file():
    return SimpleUploadedFile("invoice.pdf", b"content", content_type="application/pdf")


class TestInvoiceList:

    def test_unauthenticated_user_returns_403(self):
        client = APIClient()
        response = client.get("/api/invoices/")
        assert response.status_code == 403
        assert response.data["detail"].code == "not_authenticated"

    def test_correct_queryset_returned(self, user, mocker):
        client = APIClient()
        client.force_authenticate(user=user)
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)

        InvoiceFactory.create_batch(20, owner=user.profile)
        InvoiceFactory.create_batch(100)

        response = client.get("/api/invoices/")

        assert response.status_code == 200
        assert response.data["pagination"]["total"] == 20
        assert len(response.data["data"]) == 20

    def test_correct_queryset_returned_with_wildcard_permissions(self, user, mocker):
        client = APIClient()
        client.force_authenticate(user=user)
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.VIEW_EXPENSES: "*"},
            autospec=True,
        )

        InvoiceFactory.create_batch(100)

        response = client.get("/api/invoices/")

        assert response.status_code == 200
        assert response.data["pagination"]["total"] == 100
        count = 0
        page = 1
        while page <= response.data["pagination"]["total_pages"]:
            response = client.get(f"/api/invoices/?page={page}")
            count += len(response.data["data"])
            page += 1
        assert count == 100


class TestInvoiceCreate:

    def test_rejects_empty_file_array(self, api_client):

        data = {
            "invoice_date": YESTERDAY.strftime("%Y-%m-%d"),
            "due_date": TOMORROW.strftime("%Y-%m-%d"),
            "description": "Test description",
            "accounted": False,
            "files": [],
        }
        response = api_client.post("/api/invoices/", data=data, format="multipart")

        assert response.status_code == 400
        assert response.data["detail"].code == "invoice_file_required"

    def test_rejects_missing_file_field(self, api_client):
        data = {
            "invoice_date": YESTERDAY.strftime("%Y-%m-%d"),
            "due_date": TOMORROW.strftime("%Y-%m-%d"),
            "description": "Test description",
            "accounted": False,
        }
        response = api_client.post("/api/invoices/", data=data, format="multipart")
        assert response.status_code == 400
        assert response.data["detail"].code == "invoice_file_required"

    def test_rejects_malformed_parts_json(self, api_client):

        data = {
            "invoice_date": YESTERDAY.strftime("%Y-%m-%d"),
            "due_date": TOMORROW.strftime("%Y-%m-%d"),
            "description": "Test description",
            "accounted": False,
            "files": [
                SimpleUploadedFile(
                    "invoice.pdf", b"content", content_type="application/pdf"
                )
            ],
            "parts": "not a json",
        }
        response = api_client.post("/api/invoices/", data=data, format="multipart")

        assert response.status_code == 400
        assert response.data["detail"].code == "invoice_part_invalid_json"

    def test_rejects_missing_parts_field(self, api_client):
        data = {
            "invoice_date": YESTERDAY.strftime("%Y-%m-%d"),
            "due_date": TOMORROW.strftime("%Y-%m-%d"),
            "description": "Test description",
            "accounted": False,
            "files": [make_file()],
        }
        response = api_client.post("/api/invoices/", data=data, format="multipart")
        assert response.status_code == 400
        assert response.data["detail"].code == "invoice_part_required"

    def test_rejects_malformed_date(self, api_client):
        data = {
            "invoice_date": "20260530",
            "due_date": TOMORROW.strftime("%Y-%m-%d"),
            "description": "Test description",
            "accounted": False,
            "files": [
                SimpleUploadedFile(
                    "invoice.pdf", b"content", content_type="application/pdf"
                )
            ],
            "parts": json.dumps([PART]),
        }
        response = api_client.post("/api/invoices/", data=data, format="multipart")
        assert response.status_code == 400
        assert response.data["detail"].code == "invalid_date_format"

    def test_rejects_invoice_date_tomorrow(self, api_client):
        data = {
            "invoice_date": TOMORROW.strftime("%Y-%m-%d"),
            "due_date": TOMORROW.strftime("%Y-%m-%d"),
            "description": "Test description",
            "accounted": False,
            "files": [make_file()],
            "parts": json.dumps([PART]),
        }
        response = api_client.post("/api/invoices/", data=data, format="multipart")

        assert response.status_code == 422
        assert response.data["detail"].code == "invalid_invoice_date"

    def test_rejects_due_date_yesterday(self, api_client):
        data = {
            "invoice_date": YESTERDAY.strftime("%Y-%m-%d"),
            "due_date": YESTERDAY.strftime("%Y-%m-%d"),
            "description": "Test description",
            "accounted": False,
            "files": [make_file()],
            "parts": json.dumps([PART]),
        }

        response = api_client.post("/api/invoices/", data=data, format="multipart")
        assert response.status_code == 422
        assert response.data["detail"].code == "invalid_due_date"

    def test_rejects_accounted_without_verification(self, api_client):
        data = {
            "invoice_date": YESTERDAY.strftime("%Y-%m-%d"),
            "due_date": TOMORROW.strftime("%Y-%m-%d"),
            "description": "Test description",
            "accounted": True,
            "files": [make_file()],
            "parts": json.dumps([PART]),
        }
        response = api_client.post("/api/invoices/", data=data, format="multipart")
        assert response.status_code == 400
        assert response.data["detail"].code == "invoice_verification_required"
