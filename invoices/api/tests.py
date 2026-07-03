import datetime
import json

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from cashflow.dauth import Permission
from core.factories import UserFactory
from expenses.models import Comment
from ..factories import InvoiceFactory, InvoicePartFactory

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
            return_value={Permission.VIEW_EXPENSES: True},
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
        assert response.data["detail"].code == "file_required"

    def test_rejects_missing_file_field(self, api_client):
        data = {
            "invoice_date": YESTERDAY.strftime("%Y-%m-%d"),
            "due_date": TOMORROW.strftime("%Y-%m-%d"),
            "description": "Test description",
            "accounted": False,
        }
        response = api_client.post("/api/invoices/", data=data, format="multipart")
        assert response.status_code == 400
        assert response.data["detail"].code == "file_required"

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
        assert response.data["detail"].code == "part_invalid_json"

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
        assert response.data["detail"].code == "part_required"

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


class TestInvoicePartAttestation:

    @pytest.mark.django_db
    def test_correct_attestation(self, today, mocker):
        user = UserFactory.create()
        client = APIClient()
        client.force_authenticate(user=user)
        invoice_part = InvoicePartFactory.create(invoice__owner=user.profile)
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={
                Permission.ATTEST: [invoice_part.cost_centre],
                Permission.VIEW_EXPENSES: [invoice_part.cost_centre],
            },
        )

        response = client.post(f"/api/invoice-parts/{invoice_part.id}/attest/")

        assert response.status_code == 204
        assert response.data["attest_date"] == today.strftime("%Y-%m-%d")
        assert response.data["attested_by"]["id"] == user.profile.id

        comment = Comment.objects.filter(
            invoice=invoice_part.invoice, author=user.profile
        )
        assert comment.exists()


class TestInvoicePay:

    @pytest.mark.django_db
    def test_correct_payment(self, user, api_client, mocker, today):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.PAY: True},
            autospec=True,
        )
        invoice = InvoiceFactory.create()
        InvoicePartFactory.create(invoice=invoice, attested_by=user.profile)

        response = api_client.post(f"/api/invoices/{invoice.id}/pay/")

        assert response.status_code == 200, response.data
        assert response.data["paid_at"] == today.strftime("%Y-%m-%d")
        assert response.data["paid_by"]["username"] == user.username

        invoice.refresh_from_db()
        assert invoice.payed_by_id == user.id

    @pytest.mark.django_db
    def test_rejects_unauthorized(self, api_client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        invoice = InvoiceFactory.create()
        InvoicePartFactory.create(invoice=invoice, attested_by=invoice.owner)

        response = api_client.post(f"/api/invoices/{invoice.id}/pay/")

        assert response.status_code == 403
        assert response.data["detail"].code == "payment_permission_denied"

    @pytest.mark.django_db
    def test_rejects_already_paid(self, user, api_client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.PAY: True},
            autospec=True,
        )
        invoice = InvoiceFactory.create()
        InvoicePartFactory.create(invoice=invoice, attested_by=user.profile)
        invoice.pay(user)

        response = api_client.post(f"/api/invoices/{invoice.id}/pay/")

        assert response.status_code == 409
        assert response.data["detail"].code == "already_paid"

    @pytest.mark.django_db
    def test_rejects_unattested(self, user, api_client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.PAY: True},
            autospec=True,
        )
        invoice = InvoiceFactory.create()
        InvoicePartFactory.create(invoice=invoice, attested_by=None)

        response = api_client.post(f"/api/invoices/{invoice.id}/pay/")

        assert response.status_code == 409
        assert response.data["detail"].code == "not_payable"


class TestInvoiceAccount:

    @pytest.mark.django_db
    def test_rejects_unauthorized(self, api_client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        invoice = InvoiceFactory.create()

        response = api_client.post(
            f"/api/invoices/{invoice.id}/account/",
            {"voucher_number": "A123"},
            format="json",
        )
        assert response.status_code == 403
        assert response.data["detail"].code == "accounting_permission_denied"

    @pytest.mark.django_db
    def test_manual_voucher_number_accounts(self, user, api_client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.ACCOUNTING: True},
            autospec=True,
        )
        invoice = InvoiceFactory.create()

        response = api_client.post(
            f"/api/invoices/{invoice.id}/account/",
            {"voucher_number": "A123"},
            format="json",
        )
        assert response.status_code == 200, response.data
        invoice.refresh_from_db()
        assert invoice.verification == "A123"
        assert Comment.objects.filter(invoice=invoice, author=user.profile).exists()

    @pytest.mark.django_db
    def test_rejects_already_accounted(self, api_client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.ACCOUNTING: True},
            autospec=True,
        )
        invoice = InvoiceFactory.create(verification="A1")

        response = api_client.post(
            f"/api/invoices/{invoice.id}/account/",
            {"voucher_number": "A123"},
            format="json",
        )
        assert response.status_code == 409
        assert response.data["detail"].code == "already_accounted"

    @pytest.mark.django_db
    def test_voucher_rows_without_service_returns_503(self, api_client, mocker):
        # Without a fortnox service client attached, accounting via voucher rows
        # (rather than a manual voucher number) cannot proceed.
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.ACCOUNTING: True},
            autospec=True,
        )
        invoice = InvoiceFactory.create()

        response = api_client.post(
            f"/api/invoices/{invoice.id}/account/",
            {"voucher_rows": [{"account": 1930, "cost_centre": 100, "debit": "50.00"}]},
            format="json",
        )
        assert response.status_code == 503
        assert response.data["detail"].code == "fortnox_service_not_available"


class TestInvoiceRecommendations:
    @pytest.mark.django_db
    def test_populated_on_retrieve(self, user, api_client, mocker):
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
        invoice = InvoiceFactory.create(owner=user.profile)
        InvoicePartFactory.create(invoice=invoice)

        response = api_client.get(f"/api/invoices/{invoice.id}/")
        assert response.status_code == 200
        assert response.data["parts"][0]["recommended_accounts"] == [4010, 4011]
        # No session login, so the Fortnox service client is absent.
        assert response.data["parts"][0]["recommended_cost_centre"] is None
        assert (
            response.data["recommended_credit_account"]
            == settings.FORTNOX_INVOICE_CREDIT_ACCOUNT
        )

    @pytest.mark.django_db
    def test_null_on_list(self, user, api_client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.VIEW_EXPENSES: True},
            autospec=True,
        )
        gordian = mocker.patch(
            "cashflow.api.serializers.retrieve_account_from_gordian",
            autospec=True,
        )
        invoice = InvoiceFactory.create(owner=user.profile)
        InvoicePartFactory.create(invoice=invoice)

        response = api_client.get("/api/invoices/")
        assert response.status_code == 200
        assert response.data["data"][0]["parts"][0]["recommended_accounts"] is None
        assert response.data["data"][0]["parts"][0]["recommended_cost_centre"] is None
        assert response.data["data"][0]["recommended_credit_account"] is None
        gordian.assert_not_called()

    @pytest.mark.django_db
    def test_cost_centre_populated_with_fortnox_service(self, user, mocker):
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
        fortnox_cc.return_value.Code = "456"
        invoice = InvoiceFactory.create(owner=user.profile)
        InvoicePartFactory.create(invoice=invoice)

        response = client.get(f"/api/invoices/{invoice.id}/")
        assert response.status_code == 200
        assert response.data["parts"][0]["recommended_cost_centre"] == "456"

    @pytest.mark.django_db
    def test_account_row_without_cost_centre_is_valid(self, user, api_client, mocker):
        # Balancing rows may omit cost_centre; without a Fortnox service
        # client the request still 503s, proving it got past validation.
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.ACCOUNTING: True},
            autospec=True,
        )
        invoice = InvoiceFactory.create()

        response = api_client.post(
            f"/api/invoices/{invoice.id}/account/",
            {"voucher_rows": [{"account": 1930, "credit": "50.00"}]},
            format="json",
        )
        assert response.status_code == 503
        assert response.data["detail"].code == "fortnox_service_not_available"

    @pytest.mark.django_db
    def test_account_row_accepts_alphanumeric_cost_centre(
        self, user, api_client, mocker
    ):
        # Fortnox cost centre codes are alphanumeric (e.g. "ADAALL") and must
        # pass validation. 503 proves the payload got past it.
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.ACCOUNTING: True},
            autospec=True,
        )
        invoice = InvoiceFactory.create()

        response = api_client.post(
            f"/api/invoices/{invoice.id}/account/",
            {
                "voucher_rows": [
                    {"account": 4010, "cost_centre": "ADAALL", "debit": "50.00"}
                ]
            },
            format="json",
        )
        assert response.status_code == 503
        assert response.data["detail"].code == "fortnox_service_not_available"
