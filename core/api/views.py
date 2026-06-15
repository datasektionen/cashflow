from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db.models.aggregates import Sum, Count
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from structlog import get_logger

from core.api.filters import (
    apply_expense_filters,
    apply_invoice_filters,
    OPENAPI_PARAMS,
)
from core.api.openapi import problems
from core.api.pagination import DefaultPagination
from core.api.serializers import ClaimSerializer, ClaimData, PendingPaymentsSerializer
from core.api.utils import AuthenticatedUserMixin
from core.permissions import get_permission_provider
from expenses.models import Expense, Profile
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

        expenses = (
            Expense.objects.viewable_by(self.current_user)
            .prefetch_related("parts")
            .select_related("reimbursement")
        )
        invoices = Invoice.objects.viewable_by(self.current_user).prefetch_related(
            "parts"
        )

        expenses = apply_expense_filters(expenses, request.GET, self.current_user)
        invoices = apply_invoice_filters(invoices, request.GET, self.current_user)

        expense_data: list[ClaimData] = [
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

        invoice_data: list[ClaimData] = [
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


@extend_schema_view(
    get=extend_schema(
        tags=["Payments"],
        summary="List pending payments",
        description="Lists all users with expenses that have not been reimbursed, together with the count and total sum of non-reimbursed expenses. Only allowed for users with the `pay` permission.",
        responses={
            status.HTTP_200_OK: PendingPaymentsSerializer,
            status.HTTP_403_FORBIDDEN: problems(PermissionDenied),
        },
        operation_id="list_pending_payments",
    )
)
class PendingPaymentsList(ListAPIView, AuthenticatedUserMixin):
    """Lists available reimbursements per user."""

    def get_serializer_class(self):
        return PendingPaymentsSerializer

    def get_queryset(self):
        return (
            Profile.objects.annotate(
                count=Count("expense", filter=Q(expense__reimbursement__isnull=True))
            )
            .annotate(
                total=Sum(
                    "expense__expensepart__amount",
                    filter=Q(expense__reimbursement__isnull=True),
                )
            )
            .filter(count__gt=0)
            .filter(total__isnull=False)
            .order_by("-total")
        )

    def list(self, request, *args, **kwargs):
        if not get_permission_provider().may_pay(self.current_user):
            raise PermissionDenied()
        return super().list(request, *args, **kwargs)


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
                        "confirmable": serializers.IntegerField(),
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
        return Response(
            {
                "expenses": {
                    "attestable": Expense.objects.attestable_for(user).count(),
                    "confirmable": Expense.objects.confirmable_for(user).count(),
                    "accountable": Expense.objects.accountable_for(user).count(),
                    "payable": Expense.objects.payable_for(user).count(),
                },
                "invoices": {
                    "attestable": Invoice.objects.attestable_for(user).count(),
                    "confirmable": Invoice.objects.confirmable_for(user).count(),
                    "accountable": Invoice.objects.accountable_for(user).count(),
                    "payable": Invoice.objects.payable_for(user).count(),
                },
            }
        )
