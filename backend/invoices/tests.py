# Test factories live in invoices/factories.py (see InvoiceFactory,
# InvoiceFileFactory, InvoicePartFactory). Invoice tests go here.

from datetime import date


from cashflow.dauth import Permission
from invoices.factories import InvoiceFactory, InvoicePartFactory


class TestInvoiceListSorting:
    def test_defaults_to_created_at_desc(self, user, api_client, mocker):
        permissions = {Permission.VIEW_EXPENSES: True}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )
        first = InvoiceFactory()
        second = InvoiceFactory()

        response = api_client.get("/api/invoices/")

        assert response.status_code == 200
        ids = [i["id"] for i in response.data["data"]]
        assert ids.index(second.data_id) < ids.index(first.data_id)

    def test_sorting_by_total_desc(self, user, api_client, mocker):
        permissions = {Permission.VIEW_EXPENSES: True}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )
        cheap = InvoiceFactory()
        InvoicePartFactory(claim=cheap, amount="10.00")
        pricey = InvoiceFactory()
        InvoicePartFactory(claim=pricey, amount="100.00")

        response = api_client.get("/api/invoices/", {"sorting": "-total"})

        assert response.status_code == 200
        ids = [i["id"] for i in response.data["data"]]
        assert ids.index(pricey.data_id) < ids.index(cheap.data_id)
        totals = {i["id"]: i["total"] for i in response.data["data"]}
        assert totals[cheap.data_id] == "10.00"
        assert totals[pricey.data_id] == "100.00"

    def test_sorting_by_date_asc(self, user, api_client, mocker):
        permissions = {Permission.VIEW_EXPENSES: True}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )
        earlier = InvoiceFactory(invoice_data__invoice_date=date(2024, 1, 1))
        later = InvoiceFactory(invoice_data__invoice_date=date(2024, 6, 1))

        response = api_client.get("/api/invoices/", {"sorting": "date"})

        assert response.status_code == 200
        ids = [i["id"] for i in response.data["data"]]
        assert ids.index(earlier.data_id) < ids.index(later.data_id)


class TestInvoiceListFlaggedFilter:
    def test_flagged_true_excludes_all_invoices(self, user, api_client, mocker):
        permissions = {Permission.VIEW_EXPENSES: True}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )
        InvoiceFactory.create_batch(3)

        response = api_client.get("/api/invoices/", {"flagged": "true"})

        assert response.status_code == 200
        assert response.data["pagination"]["total"] == 0

    def test_flagged_false_keeps_all_invoices(self, user, api_client, mocker):
        permissions = {Permission.VIEW_EXPENSES: True}
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value=permissions, autospec=True
        )
        InvoiceFactory.create_batch(3)

        response = api_client.get("/api/invoices/", {"flagged": "false"})

        assert response.status_code == 200
        assert response.data["pagination"]["total"] == 3
