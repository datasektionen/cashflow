from enum import Enum

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from core.api.pagination import DefaultPagination
from core.api.serializers import ClaimSerializer
from core.api.utils import AuthenticatedUserMixin
from expenses.models import Expense
from invoices.models import Invoice

UserModel = get_user_model()


class ClaimStatus(Enum):
    SUBMITTED = "submitted"
    PAID = "paid"


def get_status(target: Expense | Invoice) -> str:
    return ClaimStatus.PAID.value if target.is_paid() else ClaimStatus.SUBMITTED.value


@extend_schema_view(
    get=extend_schema(
        tags=["Users"],
        summary="List claims",
        description="List all claims (expenses and invoices) for the given user. Admins may view any user's claims; others may only view their own.",
        responses=ClaimSerializer(many=True),
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

    def get(self, request, username):
        target = self._resolve_target_user(username)
        expenses = Expense.objects.filter(owner=target.profile)
        invoices = Invoice.objects.filter(owner=target.profile)
        data = sorted(
            [
                {
                    "type": "expense",
                    "description": expense.description,
                    "id": expense.id,
                    "amount": expense.total_amount(),
                    "status": get_status(expense),
                    "date": expense.expense_date,
                }
                for expense in expenses
            ]
            + [
                {
                    "type": "invoice",
                    "description": invoice.description,
                    "id": invoice.id,
                    "amount": invoice.total_amount(),
                    "status": get_status(invoice),
                    "date": invoice.invoice_date,
                }
                for invoice in invoices
            ],
            key=lambda x: x["date"],
            reverse=True,
        )

        page = self.paginate_queryset(data)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)
