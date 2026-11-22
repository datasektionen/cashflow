import pytest
from datetime import date
from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from hypothesis import given, settings, HealthCheck, strategies as st

from cashflow.dauth import Permission
from core.api.serializers import ClaimSerializer
from core.factories import ProfileFactory
from core.files import normalize_upload
from core.models import Claim
from core.search import fuzzy_model_search
from expenses.factories import ExpenseFactory, ExpenseFileFactory, ExpensePartFactory
from expenses.models import Payment
from invoices.factories import InvoiceFactory, InvoicePartFactory


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

        result = fuzzy_model_search(Claim.objects.all(), "utlägg", "description")

        assert match in result

    @pytest.mark.django_db
    def test_orders_by_score_best_match_first(self):
        best = ExpenseFactory(description="utlägg")
        worse = ExpenseFactory(
            description="ett långt utläg med stavfel längre bort i texten"
        )

        result = fuzzy_model_search(Claim.objects.all(), "utlägg", "description")

        assert list(result) == [best, worse]


class TestComment:

    @pytest.mark.django_db
    @settings(
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.nested_given,
        ],
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
            f"/api/{resource}/{obj.data_id}/comments/",
            {"content": comment},
        )

        assert response.status_code == 201
        assert response.data["content"] == comment.strip()

    @pytest.mark.django_db
    @settings(
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.nested_given,
        ],
    )
    @given(comment=st.text().filter(lambda s: s.strip() == "" and "\x00" not in s))
    def test_rejects_blank_comment(
        self, api_client, commentable, no_permissions, comment
    ):
        resource, obj = commentable
        response = api_client.post(
            f"/api/{resource}/{obj.data_id}/comments/",
            {"content": comment},
        )

        assert response.status_code == 400
        assert response.data["content"][0].code == "blank"


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

        response = api_client.post(f"/api/expenses/{expense.data_id}/confirm/")

        assert response.status_code == 204

    @pytest.mark.django_db
    def test_confirm_rejects_unauthorized(self, api_client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        expense = ExpenseFactory()

        response = api_client.post(f"/api/expenses/{expense.data_id}/confirm/")

        assert response.status_code == 403
        assert response.data["detail"].code == "confirmation_permission_denied"

    @pytest.mark.django_db
    def test_confirm_rejects_already_confirmed(
        self, api_client, user, confirm_permission
    ):
        # Confirm after creation: the factory attaches a File post-creation,
        # which resets any confirmation passed as a factory kwarg.
        expense = ExpenseFactory()
        expense.expense_data.confirmed_by = user
        expense.expense_data.save()

        response = api_client.post(f"/api/expenses/{expense.data_id}/confirm/")

        assert response.status_code == 409
        assert response.data["detail"].code == "already_confirmed"

    @pytest.mark.django_db
    def test_confirm_rejects_flagged(self, api_client, confirm_permission):
        expense = ExpenseFactory(expense_data__is_flagged=True)

        response = api_client.post(f"/api/expenses/{expense.data_id}/confirm/")

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
        ExpenseFactory(owner=user.profile)
        InvoiceFactory(owner=user.profile)

        response = api_client.get("/api/claims/?per_page=100")

        assert response.status_code == 200
        types = {c["type"] for c in response.data["data"]}
        assert types == {"expense", "invoice"}

    @pytest.mark.django_db
    def test_exposes_flagged_status(self, user, api_client, confirm_and_view_all):
        flagged = ExpenseFactory(owner=user.profile, expense_data__is_flagged=True)
        unflagged = ExpenseFactory(owner=user.profile, expense_data__is_flagged=False)
        invoice = InvoiceFactory(owner=user.profile)

        response = api_client.get("/api/claims/?per_page=100")

        assert response.status_code == 200
        by_id = {
            c["id"]: c["is_flagged"]
            for c in response.data["data"]
            if c["type"] == "expense"
        }
        assert by_id[flagged.data_id] is True
        assert by_id[unflagged.data_id] is False
        invoice_row = next(
            c
            for c in response.data["data"]
            if c["type"] == "invoice" and c["id"] == invoice.data_id
        )
        assert invoice_row["is_flagged"] is False

    @pytest.mark.django_db
    def test_flagged_true_excludes_invoices(
        self, user, api_client, confirm_and_view_all
    ):
        flagged = ExpenseFactory(owner=user.profile, expense_data__is_flagged=True)
        InvoiceFactory(owner=user.profile)

        response = api_client.get("/api/claims/?flagged=true&per_page=100")

        assert response.status_code == 200
        types = {c["type"] for c in response.data["data"]}
        assert types == {"expense"}
        assert [c["id"] for c in response.data["data"]] == [flagged.data_id]

    @pytest.mark.django_db
    def test_type_expense_excludes_invoices(
        self, user, api_client, confirm_and_view_all
    ):
        ExpenseFactory(owner=user.profile)
        InvoiceFactory(owner=user.profile)

        response = api_client.get("/api/claims/?type=expense&per_page=100")

        assert response.status_code == 200
        assert response.data["data"]
        assert all(c["type"] == "expense" for c in response.data["data"])

    @pytest.mark.django_db
    def test_page_query_count_is_independent_of_table_size(
        self, user, api_client, confirm_and_view_all, django_assert_max_num_queries
    ):
        for _ in range(15):
            ExpensePartFactory(claim=ExpenseFactory(owner=user.profile))
            InvoicePartFactory(claim=InvoiceFactory(owner=user.profile))

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
            ("expense", ExpenseFactory(owner=user.profile).data_id) for _ in range(7)
        } | {("invoice", InvoiceFactory(owner=user.profile).data_id) for _ in range(7)}

        seen = []
        for page in range(1, 6):
            response = api_client.get(f"/api/claims/?per_page=3&page={page}")
            assert response.status_code == 200
            seen += [(c["type"], c["id"]) for c in response.data["data"]]

        assert len(seen) == len(set(seen)) == 14
        assert set(seen) == expected

    @pytest.mark.django_db
    def test_cost_centre_filter_does_not_duplicate_multi_part_claims(
        self, user, api_client, confirm_and_view_all
    ):
        # Filtering on cost centre joins the parts table, so a claim with
        # several parts in that cost centre must still appear only once (#399).
        expense = ExpenseFactory(owner=user.profile)
        expense.parts.all().delete()
        for _ in range(3):
            ExpensePartFactory(claim=expense, cost_centre="DKM")

        invoice = InvoiceFactory(owner=user.profile)
        invoice.parts.all().delete()
        for _ in range(3):
            InvoicePartFactory(claim=invoice, cost_centre="DKM")

        response = api_client.get("/api/claims/?cost_centre=DKM&per_page=100")

        assert response.status_code == 200
        seen = [(c["type"], c["id"]) for c in response.data["data"]]
        assert sorted(seen) == sorted(
            [("expense", expense.data_id), ("invoice", invoice.data_id)]
        )
        assert response.data["pagination"]["total"] == 2

    @pytest.mark.django_db
    def test_sorting_by_date_merges_expenses_and_invoices(
        self, user, api_client, confirm_and_view_all
    ):
        earliest = ExpenseFactory(
            owner=user.profile, expense_data__expense_date=date(2024, 1, 1)
        )
        middle = InvoiceFactory(
            owner=user.profile, invoice_data__invoice_date=date(2024, 3, 1)
        )
        latest = ExpenseFactory(
            owner=user.profile, expense_data__expense_date=date(2024, 6, 1)
        )

        response = api_client.get("/api/claims/?sorting=date&per_page=100")

        assert response.status_code == 200
        keys = [(c["type"], c["id"]) for c in response.data["data"]]
        assert (
            keys.index(("expense", earliest.data_id))
            < keys.index(("invoice", middle.data_id))
            < keys.index(("expense", latest.data_id))
        )

    @pytest.mark.django_db
    def test_sorting_by_total_merges_expenses_and_invoices(
        self, user, api_client, confirm_and_view_all
    ):
        cheap = ExpenseFactory(owner=user.profile)
        cheap.parts.all().delete()
        ExpensePartFactory(claim=cheap, amount="10.00")
        middle = InvoiceFactory(owner=user.profile)
        InvoicePartFactory(claim=middle, amount="50.00")
        pricey = ExpenseFactory(owner=user.profile)
        pricey.parts.all().delete()
        ExpensePartFactory(claim=pricey, amount="100.00")

        response = api_client.get("/api/claims/?sorting=-total&per_page=100")

        assert response.status_code == 200
        keys = [(c["type"], c["id"]) for c in response.data["data"]]
        assert (
            keys.index(("expense", pricey.data_id))
            < keys.index(("invoice", middle.data_id))
            < keys.index(("expense", cheap.data_id))
        )


class TestClaimSerializer:

    @pytest.mark.django_db
    def test_serializes_annotated_claim(self):
        expense = ExpenseFactory(expense_data__expense_date=date(2024, 1, 1))
        expense.parts.all().delete()
        ExpensePartFactory(claim=expense, amount="100.00")
        ExpensePartFactory(claim=expense, amount="23.45")

        result = ClaimSerializer(Claim.objects.with_total().get(pk=expense.pk)).data

        assert result["id"] == expense.data_id
        assert result["type"] == "expense"
        assert result["amount"] == "123.45"
        assert result["expense_date"] == "2024-01-01"
        assert result["invoice_date"] is None
        assert result["is_attested"] is False
        assert result["is_paid"] is False
        assert result["voucher"] is None


class TestPendingPaymentsList:

    @pytest.mark.django_db
    def test_correct_count_and_total(self, user, api_client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions", return_value={"pay": True}, autospec=True
        )

        ExpenseFactory.create_batch(
            10,
            owner=user.profile,
            expense_data__reimbursement=Payment.objects.create(
                payer=user.profile, receiver=user.profile
            ),
        )
        pending = ExpenseFactory.create_batch(5, owner=user.profile)
        for expense in pending:
            expense.expense_data.confirmed_by = user
            expense.expense_data.save()
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
        expenses = ExpenseFactory.create_batch(5, owner=payee)
        api_client.force_authenticate(user=user)
        response = api_client.post(
            f"/api/payments/", {"expenses": [e.data_id for e in expenses]}
        )

        assert response.status_code == 201, response.data
        assert response.data["payer"]["username"] == user.username
        assert response.data["receiver"]["username"] == payee.user.username

    @pytest.mark.django_db
    def test_rejects_unauthorized(self, api_client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        payee = ProfileFactory.create()
        expenses = ExpenseFactory.create_batch(5, owner=payee)
        response = api_client.post(
            f"/api/payments/", {"expenses": [e.data_id for e in expenses]}
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
        expense = ExpenseFactory.create(
            expense_data__reimbursement=existing_payment, owner=payee
        )
        api_client.force_authenticate(user=user)

        response = api_client.post(f"/api/payments/", {"expenses": [expense.data_id]})

        assert response.status_code == 409
        assert response.data["detail"].code == "already_reimbursed"

        # check that existing reimbursement was not changed
        expense.expense_data.refresh_from_db()
        assert expense.expense_data.reimbursement_id == existing_payment.id

    @pytest.mark.django_db
    def test_rejects_multiple_receivers(self, user, api_client, mocker):
        mocker.patch(
            "cashflow.dauth.get_permissions",
            return_value={Permission.PAY: True},
            autospec=True,
        )
        expenses = ExpenseFactory.create_batch(5)
        response = api_client.post(
            f"/api/payments/", {"expenses": [e.data_id for e in expenses]}
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

    @pytest.fixture
    def confirmed(self, db, user):
        # Confirm after creation: the factory attaches a File post-creation,
        # which itself resets any confirmation passed as a factory kwarg.
        expense = ExpenseFactory()
        expense.expense_data.confirmed_by = user
        expense.expense_data.confirmed_at = date.today()
        expense.expense_data.save()
        return expense

    def test_adding_a_file_resets_confirmation(self, confirmed):
        ExpenseFileFactory(claim=confirmed)

        confirmed.expense_data.refresh_from_db()
        assert confirmed.expense_data.confirmed_by is None
        assert confirmed.expense_data.confirmed_at is None

    def test_deleting_a_file_resets_confirmation(self, confirmed):
        confirmed.file_set.first().delete()

        confirmed.expense_data.refresh_from_db()
        assert confirmed.expense_data.confirmed_by is None
        assert confirmed.expense_data.confirmed_at is None
