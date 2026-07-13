from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django.db.models.aggregates import Sum, Count
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    inline_serializer,
)
from django.db import transaction
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from structlog import get_logger

from core.api.filters import (
    apply_expense_filters,
    apply_invoice_filters,
    Filter,
    OPENAPI_PARAMS,
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
from expenses.models import Comment, Expense, ExpensePart, Payment, Profile
from fortnox import FortnoxRequest
from invoices.models import Invoice, InvoicePart

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

    def count(self) -> int:
        return self._total


@extend_schema_view(
    get=extend_schema(
        tags=["Users"],
        summary="List claims",
        description="List all claims (expenses and invoices). Defaults to the requesting user. Pass `?user=<username>` to view another user's claims (admins only).",
        responses=ClaimSerializer(many=True),
        parameters=list(OPENAPI_PARAMS.values()),
    )
)
class ClaimsList(GenericAPIView, AuthenticatedUserMixin):
    pagination_class = DefaultPagination

    def get_serializer_class(self):
        return ClaimSerializer

    def get(self, request: Request):

        claim_type = request.GET.get(Filter.TYPE)

        # Each source queryset is sliced in SQL to the rows that can appear
        # on or before the requested page, so page cost does not grow with
        # table size. Non-numeric pages ("last") materialize everything.
        window = None
        if self.paginator is not None:
            page_size = self.paginator.get_page_size(request)
            raw_page = request.GET.get(self.paginator.page_query_param, "1")
            if page_size and raw_page.isdigit():
                window = int(raw_page) * page_size

        total = 0
        expense_data: list[ClaimData] = []
        if claim_type != "invoice":
            expenses = (
                Expense.objects.viewable_by(self.current_user)
                .select_related("reimbursement", "owner__user")
                .prefetch_related(
                    Prefetch(
                        "parts",
                        ExpensePart.objects.select_related("attested_by__user"),
                    )
                )
            )
            expenses = apply_expense_filters(expenses, request.GET, self.current_user)
            total += expenses.count()
            expenses = expenses.order_by("-created_date", "-id")
            if window is not None:
                expenses = expenses[:window]
            expense_data = [
                {
                    "id": expense.id,
                    "type": "expense",
                    "description": expense.description,
                    "amount": expense.total_amount(),
                    "created_date": expense.created_date,
                    "is_attested": expense.is_attested(),
                    "is_confirmed": expense.confirmed_by_id is not None,
                    "is_paid": expense.is_paid(),
                    # Model stores "" for not-yet-accounted; API exposes null
                    "voucher": expense.verification or None,
                    "owner": expense.owner,
                    "parts": expense.parts.all(),
                }
                for expense in expenses
            ]

        invoice_data: list[ClaimData] = []
        if claim_type != "expense":
            invoices = (
                Invoice.objects.viewable_by(self.current_user)
                .select_related("owner__user")
                .prefetch_related(
                    Prefetch(
                        "parts",
                        InvoicePart.objects.select_related("attested_by__user"),
                    )
                )
            )
            invoices = apply_invoice_filters(invoices, request.GET, self.current_user)
            total += invoices.count()
            invoices = invoices.order_by("-created_date", "-id")
            if window is not None:
                invoices = invoices[:window]
            invoice_data = [
                {
                    "id": invoice.id,
                    "type": "invoice",
                    "description": invoice.description,
                    "amount": invoice.total_amount(),
                    "created_date": invoice.created_date,
                    "is_attested": invoice.is_attested(),
                    "is_confirmed": invoice.confirmed_by_id is not None,
                    "is_paid": invoice.is_paid(),
                    "voucher": invoice.verification or None,
                    "owner": invoice.owner,
                    "parts": invoice.parts.all(),
                }
                for invoice in invoices
            ]

        # The merge key must match the querysets' ordering so the per-source
        # windows and the merged window select the same rows.
        data: list[ClaimData] = sorted(
            expense_data + invoice_data,
            key=lambda x: (x["created_date"], x["id"]),
            reverse=True,
        )
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
        if not get_permission_provider().may_pay(self.current_user):
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


class VoucherSeriesList(GenericAPIView):

    def get_serializer_class(self):
        return VoucherSeriesSerializer

    def get(self, request: FortnoxRequest):

        series = []

        if request.fortnox_service is not None:
            series = [
                {"code": vs.Code, "description": vs.Description}
                for vs in request.fortnox_service.list_voucher_series()
            ]

        # Resolve voucher series from existing expenses and invoices
        expense_codes = [
            v[0].upper()
            for v in Expense.objects.all().values_list("verification", flat=True)
            if v is not None and len(v) > 0
        ]
        invoice_codes = [
            v[0].upper()
            for v in Invoice.objects.all().values_list("verification", flat=True)
            if v is not None and len(v) > 0
        ]
        inactive = [
            {"code": code}
            for code in (*expense_codes, *invoice_codes)
            if code and code not in [sc["code"] for sc in series]
        ]
        series += inactive

        page = self.paginate_queryset(series)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(VoucherSeriesSerializer(series, many=True).data)
