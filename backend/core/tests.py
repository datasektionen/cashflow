import pytest
from datetime import date
from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from hypothesis import given, settings, HealthCheck, strategies as st

from cashflow.dauth import Permission
from core.api.serializers import ClaimData, ClaimSerializer
from core.factories import ProfileFactory
from core.files import normalize_upload
from core.search import fuzzy_model_search
from expenses.factories import ExpenseFactory, ExpenseFileFactory, ExpensePartFactory
from expenses.models import Expense, Payment
from invoices.factories import InvoiceFactory, InvoiceFileFactory, InvoicePartFactory


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


class TestFuzzyModelSearch:

    @pytest.mark.django_db
    def test_not_capped_at_default_extract_limit(self):
        # rapidfuzz's process.extract defaults to limit=5; a real match
        # further down the queryset must not be dropped because of it.
        match = ExpenseFactory(description="Detta är ett utlägg för resa")
        ExpenseFactory.create_batch(10, description="Kontorsmaterial inköp")

        result = fuzzy_model_search(Expense.objects.all(), "utlägg", "description")

        assert match in result

    @pytest.mark.django_db
    def test_orders_by_score_best_match_first(self):
        best = ExpenseFactory(description="utlägg")
        worse = ExpenseFactory(
            description="ett långt utläg med stavfel längre bort i texten"
        )

        result = fuzzy_model_search(Expense.objects.all(), "utlägg", "description")

        assert list(result) == [best, worse]


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
        # Confirm after creation: the factory attaches a File post-creation,
        # which resets any confirmation passed as a factory kwarg.
        expense = ExpenseFactory()
        expense.confirmed_by = user
        expense.save()

        response = api_client.post(f"/api/expenses/{expense.id}/confirm/")

        assert response.status_code == 409
        assert response.data["detail"].code == "already_confirmed"

    @pytest.mark.django_db
    def test_confirm_rejects_flagged(self, api_client, confirm_permission):
        expense = ExpenseFactory(is_flagged=True)

        response = api_client.post(f"/api/expenses/{expense.id}/confirm/")

        assert response.status_code == 409
        assert response.data["detail"].code == "resource_is_flagged"


class TestClaimsList:

    @pytest.fixture
    def confirm_and_view_all(self, mocker):
        return mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.CONFIRM: True, "view-all": True},
            autospec=True,
        )

    @pytest.mark.django_db
    def test_lists_both_types_by_default(self, user, api_client, confirm_and_view_all):
        ExpenseFactory(owner=user.profile, confirmed_by=None)
        InvoiceFactory(owner=user.profile, confirmed_by=None)

        response = api_client.get("/api/claims/?confirmable=true&per_page=100")

        assert response.status_code == 200
        types = {c["type"] for c in response.data["data"]}
        assert types == {"expense", "invoice"}

    @pytest.mark.django_db
    def test_type_expense_excludes_invoices(
        self, user, api_client, confirm_and_view_all
    ):
        ExpenseFactory(owner=user.profile, confirmed_by=None)
        InvoiceFactory(owner=user.profile, confirmed_by=None)

        response = api_client.get(
            "/api/claims/?confirmable=true&type=expense&per_page=100"
        )

        assert response.status_code == 200
        assert response.data["data"]
        assert all(c["type"] == "expense" for c in response.data["data"])

    @pytest.mark.django_db
    def test_page_query_count_is_independent_of_table_size(
        self, user, api_client, confirm_and_view_all, django_assert_max_num_queries
    ):
        for _ in range(15):
            ExpensePartFactory(expense=ExpenseFactory(owner=user.profile))
            InvoicePartFactory(invoice=InvoiceFactory(owner=user.profile))

        with django_assert_max_num_queries(12):
            response = api_client.get("/api/claims/?per_page=5")

        assert response.status_code == 200
        assert len(response.data["data"]) == 5
        assert response.data["pagination"]["total"] == 30

    @pytest.mark.django_db
    def test_pagination_yields_every_claim_exactly_once(
        self, user, api_client, confirm_and_view_all
    ):
        expected = {
            ("expense", ExpenseFactory(owner=user.profile).id) for _ in range(7)
        } | {("invoice", InvoiceFactory(owner=user.profile).id) for _ in range(7)}

        seen: list[tuple[str, int]] = []
        for page in range(1, 6):
            response = api_client.get(f"/api/claims/?per_page=3&page={page}")
            assert response.status_code == 200
            seen += [(c["type"], c["id"]) for c in response.data["data"]]

        assert len(seen) == len(set(seen)) == 14
        assert set(seen) == expected


class TestClaimSerializer:

    def test_claim_data_matches_serializer(self):
        # Compares the defined keys of the typed dict class and serializer class
        data_fields = ClaimData.__annotations__.keys()
        serializer_fields = ClaimSerializer._declared_fields
        assert set(data_fields) == set(serializer_fields)

    def test_serializes_claim_data(self):
        from unittest.mock import MagicMock

        data: ClaimData = {
            "id": 1,
            "type": "expense",
            "description": "Lunch",
            "amount": "123.45",
            "created_date": date(2024, 1, 1),
            "is_attested": False,
            "is_confirmed": False,
            "is_paid": False,
            "voucher": None,
            "owner": MagicMock(),
            "parts": [],
        }
        result = ClaimSerializer(data).data
        assert result["amount"] == "123.45"
        assert result["created_date"] == "2024-01-01"


class TestPendingPaymentsList:

    @pytest.mark.django_db
    def test_correct_count_and_total(self, user, api_client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value={"pay": True}, autospec=True
        )

        ExpenseFactory.create_batch(
            10,
            owner=user.profile,
            reimbursement=Payment.objects.create(
                payer=user.profile, receiver=user.profile
            ),
        )
        pending = ExpenseFactory.create_batch(5, owner=user.profile, reimbursement=None)
        for expense in pending:
            expense.confirmed_by = user
            expense.save()
            expense.parts.all().update(attested_by=user.profile)
        pending_sum = sum([sum([p.amount for p in e.parts.all()]) for e in pending])

        response = api_client.get("/api/payments/pending/?per_page=100")

        assert response.status_code == 200
        entry = next(
            (
                e
                for e in response.data["data"]
                if e["owner"]["username"] == user.username
            ),
            None,
        )
        assert entry is not None
        assert entry["total"] == str(pending_sum)
        assert entry["count"] == 5


class TestPaymentCreation:

    @pytest.mark.django_db
    def test_correct_payment(self, user, api_client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.PAY: True},
            autospec=True,
        )
        payee = ProfileFactory.create()
        expenses = ExpenseFactory.create_batch(5, reimbursement=None, owner=payee)
        api_client.force_authenticate(user=user)
        response = api_client.post(
            f"/api/payments/", {"expenses": [e.id for e in expenses]}
        )

        assert response.status_code == 201, response.data
        assert response.data["payer"]["username"] == user.username
        assert response.data["receiver"]["username"] == payee.user.username

    @pytest.mark.django_db
    def test_rejects_unauthorized(self, api_client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        payee = ProfileFactory.create()
        expenses = ExpenseFactory.create_batch(5, reimbursement=None, owner=payee)
        response = api_client.post(
            f"/api/payments/", {"expenses": [e.id for e in expenses]}
        )

        assert response.status_code == 403
        assert response.data["detail"].code == "payment_permission_denied"

    @pytest.mark.django_db
    def test_rejects_empty_expenses(self, user, api_client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.PAY: True},
            autospec=True,
        )
        api_client.force_authenticate(user=user)

        response = api_client.post(f"/api/payments/", {"expenses": []})

        assert response.status_code == 422
        assert response.data["detail"].code == "no_expenses"

    @pytest.mark.django_db
    def test_rejects_already_reimbursed(self, user, api_client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.PAY: True},
            autospec=True,
        )
        payee = ProfileFactory.create()
        existing_payment = Payment.objects.create(payer=payee, receiver=payee)
        expense = ExpenseFactory.create(reimbursement=existing_payment, owner=payee)
        api_client.force_authenticate(user=user)

        response = api_client.post(f"/api/payments/", {"expenses": [expense.id]})

        assert response.status_code == 409
        assert response.data["detail"].code == "already_reimbursed"

        # check that existing reimbursement was not changed
        expense.refresh_from_db()
        assert expense.reimbursement_id == existing_payment.id

    @pytest.mark.django_db
    def test_rejects_multiple_receivers(self, user, api_client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.PAY: True},
            autospec=True,
        )
        expenses = ExpenseFactory.create_batch(5, reimbursement=None)
        response = api_client.post(
            f"/api/payments/", {"expenses": [e.id for e in expenses]}
        )

        assert response.status_code == 422
        assert response.data["detail"].code == "multiple_receivers"


def _image_upload(name, content_type):
    buffer = BytesIO()
    Image.new("RGB", (4, 4), "red").save(buffer, format="png")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


class TestNormalizeUpload:
    # A real HEIF payload needs an encoder this environment lacks; the
    # conversion is driven by content type, so a PNG payload exercises it.
    def test_converts_heif_uploads_to_jpeg(self):
        result = normalize_upload(_image_upload("Receipt.HEIC", "image/heic"))

        assert result.content_type == "image/jpeg"
        assert result.name == "Receipt.jpeg"
        with Image.open(result) as image:
            assert image.format == "JPEG"

    def test_other_uploads_are_returned_unchanged(self):
        upload = _image_upload("receipt.png", "image/png")

        assert normalize_upload(upload) is upload


class TestFileChangeResetsConfirmation:
    target_factories = {"expense": ExpenseFactory, "invoice": InvoiceFactory}
    file_factories = {"expense": ExpenseFileFactory, "invoice": InvoiceFileFactory}

    @pytest.fixture(params=["expense", "invoice"])
    def confirmed(self, request, db, user):
        # Confirm after creation: the factories attach a File post-creation,
        # which itself resets any confirmation passed as a factory kwarg.
        target = self.target_factories[request.param]()
        target.confirmed_by = user
        target.confirmed_at = date.today()
        target.save()
        return request.param, target

    def test_adding_a_file_resets_confirmation(self, confirmed):
        kind, target = confirmed

        self.file_factories[kind](**{kind: target})

        target.refresh_from_db()
        assert target.confirmed_by is None
        assert target.confirmed_at is None

    def test_deleting_a_file_resets_confirmation(self, confirmed):
        kind, target = confirmed

        target.file_set.first().delete()

        target.refresh_from_db()
        assert target.confirmed_by is None
        assert target.confirmed_at is None
