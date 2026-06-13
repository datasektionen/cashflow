from django.contrib.auth import get_user_model
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from core.api.filters import (
    apply_expense_filters,
    apply_invoice_filters,
    OPENAPI_PARAMS,
)
from core.api.pagination import DefaultPagination
from core.api.serializers import ClaimSerializer, ClaimData
from core.api.utils import AuthenticatedUserMixin
from expenses.models import Expense
from invoices.models import Invoice

UserModel = get_user_model()


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

    def _resolve_target_user(self, username):
        if username == self.current_user.username:
            return self.current_user
        if not self.current_user.profile.may_view_all():
            raise PermissionDenied(
                "You do not have permission to view other users' claims."
            )
        try:
            return UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            raise NotFound(f"User '{username}' not found.")

    def get(self, request: Request):
        username = request.GET.get("user", self.current_user.username)
        target = self._resolve_target_user(username)

        expenses = Expense.objects.viewable_by(self.current_user)
        invoices = Invoice.objects.viewable_by(self.current_user)

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
