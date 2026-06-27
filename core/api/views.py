from django.contrib.auth import get_user_model
from django.db.models import Q
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
)
from core.api.utils import AuthenticatedUserMixin
from core.permissions import get_permission_provider
from expenses.models import Comment, Expense, Payment, Profile
from invoices.models import Invoice

UserModel = get_user_model()
logger = get_logger(__name__)


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

        expense_data: list[ClaimData] = []
        if claim_type != "invoice":
            expenses = (
                Expense.objects.viewable_by(self.current_user)
                .prefetch_related("parts")
                .select_related("reimbursement")
            )
            expenses = apply_expense_filters(expenses, request.GET, self.current_user)
            expense_data = [
                {
                    "id": expense.id,
                    "type": "expense",
                    "description": expense.description,
                    "amount": expense.total_amount(),
                    "created_date": expense.created_date,
                    "is_attested": expense.is_attested(),
                    "is_confirmed": expense.confirmed_by is not None,
                    "is_paid": expense.is_paid(),
                    "owner": expense.owner,
                    "parts": expense.parts.all(),
                }
                for expense in expenses
            ]

        invoice_data: list[ClaimData] = []
        if claim_type != "expense":
            invoices = Invoice.objects.viewable_by(self.current_user).prefetch_related(
                "parts"
            )
            invoices = apply_invoice_filters(invoices, request.GET, self.current_user)
            invoice_data = [
                {
                    "id": invoice.id,
                    "type": "invoice",
                    "description": invoice.description,
                    "amount": invoice.total_amount(),
                    "created_date": invoice.created_date,
                    "is_attested": invoice.is_attested(),
                    "is_confirmed": invoice.confirmed_by is not None,
                    "is_paid": invoice.is_paid(),
                    "owner": invoice.owner,
                    "parts": invoice.parts.all(),
                }
                for invoice in invoices
            ]

        data: list[ClaimData] = sorted(
            expense_data + invoice_data,
            key=lambda x: x["created_date"],
            reverse=True,
        )

        page: list[Expense | Invoice] | None = self.paginate_queryset(data)  # type: ignore[arg-type]
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(data, many=True)
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
