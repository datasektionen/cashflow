import json

import pytest

from expenses.factories import ExpenseFactory


@pytest.mark.django_db
class TestExpenseSearchAction:
    def test_returns_matching_expenses(self, user, client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        match = ExpenseFactory(description="Coffee machine repair", owner=user.profile)
        ExpenseFactory(description="Office chairs", owner=user.profile)

        response = client.post(
            "/api/expenses/search/",
            {"query": {"description": "coffee"}},
            format="json",
        )

        assert response.status_code == 200
        assert [e["id"] for e in response.data["data"]] == [match.id]
        assert response.data["pagination"]["total"] == 1

    def test_query_method_also_works(self, user, client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        match = ExpenseFactory(description="Coffee machine repair", owner=user.profile)
        ExpenseFactory(description="Office chairs", owner=user.profile)

        response = client.generic(
            "QUERY",
            "/api/expenses/search/",
            data=json.dumps({"query": {"description": "coffee"}}),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert [e["id"] for e in response.data["data"]] == [match.id]

    def test_query_with_filter_fields(self, user, client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        accounted = ExpenseFactory(verification="A123", owner=user.profile)
        ExpenseFactory(verification="", owner=user.profile)

        response = client.post(
            "/api/expenses/search/",
            {"query": {"accounted": True}},
            format="json",
        )

        assert response.status_code == 200
        assert [e["id"] for e in response.data["data"]] == [accounted.id]

    def test_pagination_via_url_query_string(self, user, client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        ExpenseFactory.create_batch(3, description="Coffee", owner=user.profile)

        response = client.post(
            "/api/expenses/search/?page=2&per_page=1",
            {"query": {"description": "coffee"}},
            format="json",
        )

        assert response.status_code == 200
        assert len(response.data["data"]) == 1
        assert response.data["pagination"]["page"] == 2
        assert response.data["pagination"]["per_page"] == 1
        assert response.data["pagination"]["total"] == 3
