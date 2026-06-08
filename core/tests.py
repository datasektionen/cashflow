import pytest
from hypothesis import given, settings, HealthCheck, strategies as st

from expenses.factories import ExpenseFactory
from invoices.factories import InvoiceFactory


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

        assert response.status_code == 400
        assert response.data["detail"].code == "empty_comment"
