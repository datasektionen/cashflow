import pytest
from datetime import date
from hypothesis import given, settings, HealthCheck, strategies as st

from cashflow.dauth import Permission
from core.api.serializers import ClaimData, ClaimSerializer
from expenses.factories import ExpenseFactory
from invoices.factories import InvoiceFactory


def implies(a: bool, b: bool) -> bool:
    return not a or b


@pytest.fixture
def no_permissions(mocker):
    return mocker.patch(
        "cashflow.dauth.get_permissions", return_value={}, autospec=True
    )


@pytest.fixture(params=["expenses", "invoices"])
def commentable(request, user):
    factories = {"expenses": ExpenseFactory, "invoices": InvoiceFactory}
    resource = request.param
    obj = factories[resource](owner=user.profile)
    return resource, obj


class TestComment:

    @pytest.mark.django_db
    @settings(
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.nested_given,
        ]
    )
    @given(
        comment=st.text(alphabet=st.characters(codec="utf-8"), min_size=1).filter(
            lambda s: s.strip() and "\x00" not in s
        )
    )
    def test_accepts_valid_comment(
        self, api_client, commentable, no_permissions, comment
    ):
        resource, obj = commentable
        response = api_client.post(
            f"/api/{resource}/{obj.id}/comments/",
            {"content": comment},
        )

        assert response.status_code == 201
        assert response.data["content"] == comment.strip()

    @pytest.mark.django_db
    @settings(
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.nested_given,
        ]
    )
    @given(comment=st.text().filter(lambda s: s.strip() == "" and "\x00" not in s))
    def test_rejects_blank_comment(
        self, api_client, commentable, no_permissions, comment
    ):
        resource, obj = commentable
        response = api_client.post(
            f"/api/{resource}/{obj.id}/comments/",
            {"content": comment},
        )

        assert response.status_code == 422
        assert response.data["detail"].code == "empty_comment"


class TestConfirmation:

    @pytest.fixture
    def confirm_permission(self, mocker):
        return mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.CONFIRM: True},
            autospec=True,
        )

    @pytest.mark.django_db
    def test_confirm_succeeds(self, api_client, user, confirm_permission, today):
        expense = ExpenseFactory()

        response = api_client.post(f"/api/expenses/{expense.id}/confirm/")

        assert response.status_code == 204

    @pytest.mark.django_db
    def test_confirm_rejects_unauthorized(self, api_client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        expense = ExpenseFactory()

        response = api_client.post(f"/api/expenses/{expense.id}/confirm/")

        assert response.status_code == 403
        assert response.data["detail"].code == "confirmation_permission_denied"

    @pytest.mark.django_db
    def test_confirm_rejects_already_confirmed(
        self, api_client, user, confirm_permission
    ):
        expense = ExpenseFactory(confirmed_by=user)

        response = api_client.post(f"/api/expenses/{expense.id}/confirm/")

        assert response.status_code == 409
        assert response.data["detail"].code == "already_confirmed"

    @pytest.mark.django_db
    def test_confirm_rejects_flagged(self, api_client, confirm_permission):
        expense = ExpenseFactory(is_flagged=True)

        response = api_client.post(f"/api/expenses/{expense.id}/confirm/")

        assert response.status_code == 409
        assert response.data["detail"].code == "resource_is_flagged"


class TestClaimSerializer:

    def test_claim_data_matches_serializer(self):
        # Compares the defined keys of the typed dict class and serializer class
        data_fields = ClaimData.__annotations__.keys()
        serializer_fields = ClaimSerializer._declared_fields
        assert set(data_fields) == set(serializer_fields)

    def test_serializes_claim_data(self):
        data: ClaimData = {
            "id": 1,
            "type": "expense",
            "description": "Lunch",
            "amount": "123.45",
            "created_date": date(2024, 1, 1),
            "is_attested": False,
            "is_confirmed": False,
            "is_paid": False,
            "parts": [],
        }
        result = ClaimSerializer(data).data
        assert result["amount"] == "123.45"
        assert result["created_date"] == "2024-01-01"
