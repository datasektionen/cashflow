import pytest

from core.models import Claim
from core.search import claim_search
from expenses.factories import ExpenseFactory


@pytest.mark.django_db
class TestExpenseSearch:
    def test_description_fuzzy_matches_typo(self):
        match = ExpenseFactory(description="Coffee machine repair")
        ExpenseFactory(description="Train tickets to Gothenburg")

        result = claim_search(
            Claim.objects.all(), description_fuzzy="Cofee machne repair"
        )

        assert list(result) == [match]

    def test_no_search_fields_returns_all(self):
        ExpenseFactory.create_batch(3)

        result = claim_search(Claim.objects.all())

        assert result.count() == 3


@pytest.mark.django_db
class TestExpenseListSearchFilters:
    def test_q_matches_description(self, user, client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        match = ExpenseFactory(description="Coffee machine repair", owner=user.profile)
        ExpenseFactory(description="Office chairs", owner=user.profile)

        response = client.get("/api/expenses/", {"q": "coffee"})

        assert response.status_code == 200
        assert [e["id"] for e in response.data["data"]] == [match.data_id]
        assert response.data["pagination"]["total"] == 1

    def test_accounted_true_returns_only_accounted(self, user, client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        accounted = ExpenseFactory(verification="A123", owner=user.profile)
        ExpenseFactory(verification="", owner=user.profile)

        response = client.get("/api/expenses/", {"accounted": "true"})

        assert response.status_code == 200
        assert [e["id"] for e in response.data["data"]] == [accounted.data_id]

    def test_accounted_false_returns_only_unaccounted(self, user, client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        ExpenseFactory(verification="A123", owner=user.profile)
        unaccounted = ExpenseFactory(verification="", owner=user.profile)

        response = client.get("/api/expenses/", {"accounted": "false"})

        assert response.status_code == 200
        assert [e["id"] for e in response.data["data"]] == [unaccounted.data_id]

    def test_pagination_via_query_string(self, user, client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        ExpenseFactory.create_batch(3, description="Coffee", owner=user.profile)

        response = client.get(
            "/api/expenses/", {"q": "coffee", "page": 2, "per_page": 1}
        )

        assert response.status_code == 200
        assert len(response.data["data"]) == 1
        assert response.data["pagination"]["page"] == 2
        assert response.data["pagination"]["per_page"] == 1
        assert response.data["pagination"]["total"] == 3
