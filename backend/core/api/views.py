from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import CharField, Prefetch, Q, Value
from django.db.models.aggregates import Sum, Count
from django.db.models.functions import Cast, Concat
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from structlog import get_logger

from core.api.filters import (
    apply_expense_filters,
    apply_invoice_filters,
    ClaimQuerySerializer,
    Filter,
    Sorting,
)
from core.api.openapi import problems
from core.api.pagination import DefaultPagination
from core.api.problems import (
    MultipleReceiversProblem,
    PaymentPermissionDeniedProblem,
    AlreadyReimbursedProblem,
    NoExpensesProblem,
)
from core.api.serializers import (
    ClaimSerializer,
    ClaimData,
    PaymentCreateSerializer,
    PaymentSerializer,
    PendingPaymentsSerializer,
    VoucherSeriesSerializer,
)
from core.api.utils import AuthenticatedUserMixin
from core.permissions import get_permission_provider
from expenses.models import (
    Comment,
    Expense,
    ExpensePart,
    Payment,
    Profile,
    ExpenseQuerySet,
)
from fortnox import FortnoxRequest, FortnoxNotFound, FortnoxServiceNotAvailableProblem
from invoices.models import Invoice, InvoicePart, InvoiceQuerySet

UserModel = get_user_model()
logger = get_logger(__name__)


class _WindowedClaims(list):
    """The first rows of the merged claims feed plus the true combined count.

    Django's ``Paginator`` calls ``count()`` when the object list provides
    one, so the view can hand over a window of only the rows that can appear
    on or before the requested page while the reported totals stay correct.
    """

    def __init__(self, rows, total: int):
        super().__init__(rows)
        self._total = total

    def count(self, *_, **__) -> int:
        return self._total


@extend_schema_view(
    get=extend_schema(
        tags=["Users"],
        summary="List claims",
        description="List all claims (expenses and invoices). Defaults to the requesting user. Pass `?user=<username>` to view another user's claims (admins only).",
        responses=ClaimSerializer(many=True),
        parameters=[ClaimQuerySerializer],
    )
)
class ClaimsList(GenericAPIView, AuthenticatedUserMixin):
    pagination_class = DefaultPagination

    def get_serializer_class(self):
        return ClaimSerializer

    def get(self, request: Request):

        claim_type = request.GET.get(Filter.TYPE)

        query = ClaimQuerySerializer(data=request.GET)
        query.is_valid(raise_exception=True)
        sorting = Sorting(query.validated_data["sorting"])
        reverse = sorting in (
            Sorting.CREATED_AT_DESC,
            Sorting.DATE_DESC,
            Sorting.TOTAL_DESC,
        )
        date_sort = sorting in (Sorting.DATE_ASC, Sorting.DATE_DESC)
        total_sort = sorting in (Sorting.TOTAL_ASC, Sorting.TOTAL_DESC)

        def sort_value(total: Decimal, item_date: date | None, created: date):
            """The value each row is sorted on, matching the SQL ordering the
            source querysets were sliced by."""
            if total_sort:
                return total
            if date_sort:
                return item_date or date.min
            return created

        # Each source queryset is sliced in SQL to the rows that can appear
        # on or before the requested page, so page cost does not grow with
        # table size. Non-numeric pages ("last") materialize everything.
        window = None
        if isinstance(self.paginator, DefaultPagination):
            page_size = self.paginator.get_page_size(request)
            raw_page = request.GET.get(self.paginator.page_query_param, "1")
            if page_size and raw_page.isdigit():
                window = int(raw_page) * page_size

        total = 0
        rows: list[tuple[ClaimData, date]] = []
        if claim_type != "invoice":
            expenses: ExpenseQuerySet = (
                Expense.objects.viewable_by(self.current_user)
                .select_related("reimbursement", "owner__user")
                .prefetch_related(
                    Prefetch(
                        "parts",
                        ExpensePart.objects.select_related("attested_by__user"),
                    )
                )
                .annotate(total=Sum("expensepart__amount"))
            )
            expenses = apply_expense_filters(
                expenses, request.GET, self.current_user
            ).distinct()
            total += expenses.count()
            if window is not None:
                expenses = expenses[:window]
            rows += [
                (
                    {
                        "id": expense.id,
                        "type": "expense",
                        "description": expense.description,
                        "amount": expense.total_amount().to_eng_string(),
                        "created_date": expense.created_date,
                        "is_attested": expense.is_attested(),
                        "is_confirmed": expense.confirmed_by_id is not None,
                        "is_paid": expense.is_paid(),
                        "is_flagged": expense.is_flagged,
                        "voucher": expense.verification or None,
                        "owner": expense.owner,
                        "parts": expense.parts.all(),
                    },
                    sort_value(
                        expense.total_amount(),
                        expense.expense_date,
                        expense.created_date,
                    ),
                )
                for expense in expenses
            ]

        if claim_type != "expense":
            invoices: InvoiceQuerySet = (
                Invoice.objects.viewable_by(self.current_user)
                .select_related("owner__user")
                .prefetch_related(
                    Prefetch(
                        "parts",
                        InvoicePart.objects.select_related("attested_by__user"),
                    )
                )
                .annotate(total=Sum("invoicepart__amount"))
            )
            # See the expense branch: cost-centre and similar filters join
            # `invoicepart`, so `.distinct()` collapses the per-part duplicates.
            invoices = apply_invoice_filters(
                invoices, request.GET, self.current_user
            ).distinct()
            total += invoices.count()
            if window is not None:
                invoices = invoices[:window]
            rows += [
                (
                    {
                        "id": invoice.id,
                        "type": "invoice",
                        "description": invoice.description,
                        "amount": invoice.total_amount(),
                        "created_date": invoice.created_date,
                        "is_attested": invoice.is_attested(),
                        "is_confirmed": invoice.confirmed_by_id is not None,
                        "is_paid": invoice.is_paid(),
                        "is_flagged": False,
                        "voucher": invoice.verification or None,
                        "owner": invoice.owner,
                        "parts": invoice.parts.all(),
                    },
                    sort_value(
                        invoice.total_amount(),
                        invoice.invoice_date,
                        invoice.created_date,
                    ),
                )
                for invoice in invoices
            ]

        rows.sort(key=lambda row: row[0]["id"], reverse=True)
        if sorting != Sorting.ID_DESC:
            rows.sort(key=lambda row: row[1], reverse=reverse)
        data: list[ClaimData] = [claim for claim, _ in rows]
        if window is not None:
            data = data[:window]

        results = _WindowedClaims(data, total)
        page: list[ClaimData] | None = self.paginate_queryset(results)  # type: ignore[arg-type]
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)


class PaymentViewSet(viewsets.GenericViewSet, AuthenticatedUserMixin):
    """
    Payments (expense reimbursements).

    A payment reimburses one member for a batch of their expenses. Invoice
    payments are a different flow (a per-invoice action on the invoice) and are
    intentionally not handled here — see ``Invoice.pay``.
    """

    pagination_class = DefaultPagination

    def get_serializer_class(self):
        if self.action == "create":
            return PaymentCreateSerializer
        if self.action == "pending":
            return PendingPaymentsSerializer
        return PaymentSerializer



    @extend_schema(
        tags=["Payments"],
        summary="List payments",
        operation_id="list_payments"
    )
    def list(self, request: Request) -> Response:
        if not get_permission_provider().may_pay(self.current_user) and not get_permission_provider().may_view_all(self.current_user):
            return Response(status=status.HTTP_403_FORBIDDEN)

        payments = Payment.objects.all().order_by("-date")

        if tag := request.query_params.get("tag"):
            payments = payments.annotate(
                tag=Concat(
                    Value(settings.PAYMENT_TAG_PREFIX),
                    Cast("pk", CharField()),
                )
            ).filter(tag__icontains=tag)

        page = self.paginate_queryset(payments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Payments"],
        summary="Create a payment",
        description="Reimburses a single member for the given expenses in one payment. All expenses must belong to the same user and be confirmed and fully attested.",
        responses={
            status.HTTP_201_CREATED: PaymentSerializer,
            status.HTTP_403_FORBIDDEN: problems(PaymentPermissionDeniedProblem),
            status.HTTP_409_CONFLICT: problems(AlreadyReimbursedProblem),
            status.HTTP_422_UNPROCESSABLE_ENTITY: problems(
                MultipleReceiversProblem, NoExpensesProblem
            ),
        },
        operation_id="create_payment",
    )
    def create(self, request: Request) -> Response:
        if not get_permission_provider().may_pay(self.current_user):
            raise PaymentPermissionDeniedProblem()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expenses: list[Expense] = serializer.validated_data["expenses"]

        if not all(expense.reimbursement is None for expense in expenses):
            raise AlreadyReimbursedProblem(
                detail="One or more expenses are already reimbursed."
            )

        receivers = {expense.owner_id for expense in expenses}
        if len(receivers) > 1:
            raise MultipleReceiversProblem()

        receiver = expenses[0].owner

        with transaction.atomic():
            payment = Payment.objects.create(
                payer=self.current_user.profile, receiver=receiver
            )
            for expense in expenses:
                expense.reimbursement = payment
                expense.save(update_fields=["reimbursement"])
                Comment.objects.create(
                    author=self.current_user.profile,
                    expense=expense,
                    content=f"Betalade ut i betalning {payment.id}",
                )

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Payments"],
        summary="List pending payments",
        description="Lists all users with expenses that have not been reimbursed, together with the count and total sum of non-reimbursed expenses. Only allowed for users with the `pay` permission.",
        responses={
            status.HTTP_200_OK: PendingPaymentsSerializer,
            status.HTTP_403_FORBIDDEN: problems(PermissionDenied),
        },
        operation_id="list_pending_payments",
    )
    @action(detail=False, methods=["GET"])
    def pending(self, request: Request) -> Response:
        if not get_permission_provider().may_pay(
            self.current_user
        ) and not get_permission_provider().may_view_all(self.current_user):
            raise PermissionDenied()

        payable = Q(
            expense__reimbursement__isnull=True,
            expense__confirmed_by__isnull=False,
            expense__expensepart__attested_by__isnull=False,
        )
        queryset = (
            Profile.objects.annotate(
                count=Count("expense", filter=payable, distinct=True)
            )
            .annotate(total=Sum("expense__expensepart__amount", filter=payable))
            .filter(count__gt=0)
            .filter(total__isnull=False)
            .order_by("-total")
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        tags=["Users"],
        summary="Count available actions",
        description="Returns the number of expenses and invoices that the user can act on.",
        request=None,
        responses=inline_serializer(
            name="Summary",
            fields={
                "expenses": inline_serializer(
                    name="ExpenseSummary",
                    fields={
                        "attestable": serializers.IntegerField(),
                        "confirmable": serializers.IntegerField(),
                        "accountable": serializers.IntegerField(),
                        "payable": serializers.IntegerField(),
                    },
                ),
                "invoices": inline_serializer(
                    name="InvoiceSummary",
                    fields={
                        "attestable": serializers.IntegerField(),
                        "accountable": serializers.IntegerField(),
                        "payable": serializers.IntegerField(),
                    },
                ),
            },
        ),
    )
)
class ActionSummary(GenericAPIView, AuthenticatedUserMixin):

    def get(self, request: Request):
        user = self.current_user
        expenses = Expense.objects.viewable_by(user)
        invoices = Invoice.objects.viewable_by(user)
        return Response(
            {
                "expenses": {
                    "attestable": expenses.attestable_for(user).count(),
                    "confirmable": expenses.confirmable_for(user).count(),
                    "accountable": expenses.accountable_for(user).count(),
                    "payable": expenses.payable_for(user).count(),
                },
                "invoices": {
                    "attestable": invoices.attestable_for(user).count(),
                    "accountable": invoices.accountable_for(user).count(),
                    "payable": invoices.payable_for(user).count(),
                },
            }
        )


def _counts_by_cost_centre(
    expense_qs: "ExpenseQuerySet", invoice_qs: "InvoiceQuerySet"
) -> list[dict[str, object]]:
    """Merges expense and invoice counts grouped by their part's cost centre.

    A claim is counted once per cost centre it has a (matching) part in, so the
    same claim can contribute to several cost centres. Counts are summed across
    expenses and invoices and returned sorted by descending count.
    """
    counts: dict[str, int] = defaultdict(int)
    for row in (
        expense_qs.order_by()
        .values("expensepart__cost_centre")
        .annotate(count=Count("id", distinct=True))
    ):
        counts[row["expensepart__cost_centre"]] += row["count"]
    for row in (
        invoice_qs.order_by()
        .values("invoicepart__cost_centre")
        .annotate(count=Count("id", distinct=True))
    ):
        counts[row["invoicepart__cost_centre"]] += row["count"]
    return [
        {"cost_centre": cost_centre, "count": count}
        for cost_centre, count in sorted(
            counts.items(), key=lambda item: item[1], reverse=True
        )
    ]


def _counts_by_owner(
    expense_qs: "ExpenseQuerySet", invoice_qs: "InvoiceQuerySet"
) -> list[dict[str, object]]:
    """Merges expense and invoice counts grouped by the owning user.

    Each claim has a single owner, so counts sum to the overall total. Returned
    sorted by descending count.
    """
    owners: dict[str, dict[str, object]] = {}
    for qs in (expense_qs, invoice_qs):
        for row in (
            qs.order_by()
            .values(
                "owner__user__username",
                "owner__user__first_name",
                "owner__user__last_name",
            )
            .annotate(count=Count("id", distinct=True))
        ):
            username = row["owner__user__username"]
            owner = owners.setdefault(
                username,
                {
                    "username": username,
                    "first_name": row["owner__user__first_name"],
                    "last_name": row["owner__user__last_name"],
                    "count": 0,
                },
            )
            owner["count"] = int(owner["count"]) + row["count"]
    return sorted(owners.values(), key=lambda owner: owner["count"], reverse=True)


class ActionOverview(GenericAPIView, AuthenticatedUserMixin):

    def get(self, request: Request):
        user = self.current_user
        expenses = Expense.objects.viewable_by(user)
        invoices = Invoice.objects.viewable_by(user)
        return Response(
            {
                "attest": _counts_by_cost_centre(
                    expenses.attestable_for(user), invoices.attestable_for(user)
                ),
                "account": _counts_by_cost_centre(
                    expenses.accountable_for(user), invoices.accountable_for(user)
                ),
                "confirm": _counts_by_cost_centre(
                    expenses.confirmable_for(user), Invoice.objects.none()
                ),
                "pay": _counts_by_owner(
                    expenses.payable_for(user), invoices.payable_for(user)
                ),
            }
        )


class VoucherSeriesList(GenericAPIView):

    def get_serializer_class(self):
        return VoucherSeriesSerializer

    def get(self, request: FortnoxRequest):

        series: list[dict[str, str | None]] = []

        include_fortnox = request.GET.get("include_fortnox", "true").lower() != "false"

        if request.fortnox_service is not None and include_fortnox:
            by_code: dict[str, str | None] = {}
            try:
                for vs in request.fortnox_service.list_voucher_series():
                    if vs.Code.isalpha() and len(vs.Code) == 1:
                        by_code.setdefault(vs.Code, vs.Description)
                series = [
                    {"code": code, "description": description}
                    for code, description in by_code.items()
                ]
            except FortnoxNotFound as e:
                # Indicates the fortnox integration is disconnected
                raise FortnoxServiceNotAvailableProblem(
                    detail="Fetching voucher series from Fortnox failed, this most likely means the integration "
                    "is unavailable."
                ) from e

        # Resolve voucher series from existing expenses and invoices
        expense_codes = {
            v[0].upper()
            for v in Expense.objects.all().values_list("verification", flat=True)
            if v is not None and len(v) > 0 and v[0].isalpha()
        }
        invoice_codes = {
            v[0].upper()
            for v in Invoice.objects.all().values_list("verification", flat=True)
            if v is not None and len(v) > 0 and v[0].isalpha()
        }
        inactive: list[dict[str, str | None]] = [
            {"code": code}
            for code in expense_codes | invoice_codes
            if code and code not in [sc["code"] for sc in series]
        ]
        series += inactive

        page: list[dict[str, str | None]] | None = self.paginate_queryset(series)  # type: ignore[arg-type]
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(VoucherSeriesSerializer(series, many=True).data)
