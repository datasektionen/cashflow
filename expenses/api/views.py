"""
API views for expense management.

This module contains all REST API endpoints related to expenses, including
creating, retrieving, updating, and deleting expense records. Each view
handles HTTP request validation, permission checks, and returns JSON responses.

New endpoints should be registered in api/urls.py and follow the existing
patterns for authentication and error handling found in this file.
"""

import json

from django.contrib.auth import get_user_model
from django.db import transaction
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import generics, status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_400_BAD_REQUEST,
    HTTP_201_CREATED,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_403_FORBIDDEN,
    HTTP_204_NO_CONTENT,
)
from structlog import get_logger

from core.api.exceptions import (
    PartInvalidJSONError,
    FileRequiredError,
    PartRequiredError,
    AttestationPermissionDenied,
)
from core.api.filters import Filter
from core.api.openapi import problem, problems
from core.api.serializers import CommentSerializer, CommentCreateSerializer
from core.api.utils import AuthenticatedUserMixin
from core.exceptions import (
    UnauthorizedAttestationError,
    SelfAttestationError,
    EmptyCommentError,
)
from expenses.api.exceptions import InvalidExpenseDateError
from expenses.api.serializers import (
    ExpensePartSerializer,
    ExpenseSerializer,
    ExpenseAdminSerializer,
    ExpenseCreateSerializer,
)
from expenses.models import Expense, ExpensePart, File, Comment

UserModel = get_user_model()

logger = get_logger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="List expenses",
        description=(
            "Returns the paginated set of claims the requesting user is "
            "allowed to see. Supports optional filtering by owner via "
            "`?user=<username>` and by cost centre via `?cost_center=<name>`."
        ),
        operation_id="list_expenses",
        tags=["Expenses"],
        responses={
            HTTP_200_OK: ExpenseAdminSerializer,
            HTTP_401_UNAUTHORIZED: problem(NotAuthenticated),
        },
    ),
    retrieve=extend_schema(
        summary="Retrieve an expense",
        description=(
            "Returns a single expense by ID, including its parts, owner "
            "profile, and attached files."
        ),
        operation_id="retrieve_expense",
        tags=["Expenses"],
    ),
    create=extend_schema(
        summary="Create a new expense",
        request={"multipart/form-data": ExpenseCreateSerializer},
        description=(
            "Creates an expense together with its parts and one or more "
            "attached receipt files. Submit as `multipart/form-data` with "
            "the `parts` field as a JSON-encoded array; at least one file "
            "is required."
        ),
        responses={
            HTTP_201_CREATED: ExpenseSerializer,
            HTTP_400_BAD_REQUEST: problems(
                FileRequiredError, PartRequiredError, PartInvalidJSONError
            ),
            HTTP_401_UNAUTHORIZED: problem(NotAuthenticated),
            HTTP_422_UNPROCESSABLE_ENTITY: problem(InvalidExpenseDateError),
        },
        operation_id="create_expense",
        tags=["Expenses"],
    ),
    update=extend_schema(
        summary="Update an expense",
        description=(
            "Replaces an expense in full. All writable fields must be " "provided."
        ),
        operation_id="update_expense",
        tags=["Expenses"],
    ),
    partial_update=extend_schema(
        summary="Partially update an expense",
        description=(
            "Updates a subset of fields on an existing expense. Only the "
            "fields included in the request body are changed."
        ),
        operation_id="partial_update_expense",
        tags=["Expenses"],
    ),
    destroy=extend_schema(
        summary="Delete an expense",
        description="Permanently deletes an expense and its associated parts.",
        operation_id="delete_expense",
        tags=["Expenses"],
    ),
    comment=extend_schema(
        summary="Comment on an expense",
        description="Adds a comment to an expense. The author and date will be set automatically.",
        request=CommentCreateSerializer,
        responses={
            status.HTTP_201_CREATED: CommentSerializer,
            status.HTTP_400_BAD_REQUEST: problems(EmptyCommentError),
        },
        operation_id="add_expense_comment",
        tags=["Expenses"],
    ),
)
class ExpenseViewSet(viewsets.ModelViewSet, AuthenticatedUserMixin):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return ExpenseSerializer
        if self.current_user.profile.may_attest_some():
            return ExpenseAdminSerializer
        return ExpenseSerializer

    def create(self, request, *args, **kwargs):

        files = request.FILES.getlist("files")
        if not files:
            raise FileRequiredError()

        data = (
            request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
        )
        if isinstance(data.get("parts"), str):
            try:
                data["parts"] = json.loads(data["parts"])
            except json.JSONDecodeError:
                raise PartInvalidJSONError()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            expense = serializer.save(owner=self.current_user.profile)
            for f in files:
                File.objects.create(expense=expense, file=f)

        return Response(ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)

    def get_queryset(self):

        filter_map = {}
        if self.request.GET.get(Filter.USER):
            try:
                filtered_user = UserModel.objects.get(
                    username=self.request.GET.get(Filter.USER)
                )
                filter_map["owner__user"] = filtered_user
            except UserModel.DoesNotExist:
                pass
        if self.request.GET.get(Filter.COST_CENTER):
            filter_map["expensepart__cost_centre__in"] = [
                self.request.GET.get(Filter.COST_CENTER)
            ]

        return (
            Expense.objects.viewable_by(self.current_user)
            .filter(**filter_map)
            .distinct()
            .order_by("-expense_date")
        )

    @action(detail=True, methods=["POST"], url_path="comments")
    def comment(self, request: Request, pk=None) -> Response:
        expense = self.get_object()

        serializer = CommentCreateSerializer(data=request.data)
        if serializer.is_valid():
            comment = Comment.objects.create(
                expense=expense,
                content=serializer.validated_data["content"],
                author=self.current_user.profile,
            )
            return Response(
                CommentSerializer(comment).data, status=status.HTTP_201_CREATED
            )
        else:
            errors = serializer.errors
            if errors.get("content"):
                if errors["content"][0].code == "blank":
                    raise EmptyCommentError()

            raise serializers.ValidationError(errors)


class ExpensePartAttestView(
    generics.GenericAPIView[ExpensePart], AuthenticatedUserMixin
):
    serializer_class = ExpensePartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ExpensePart.objects.filter(
            expense__in=Expense.objects.viewable_by(self.current_user)
        )

    @extend_schema(
        tags=["Expenses"],
        summary="Attest an expense part",
        description="Attests an expense part. Submit as an empty POST request.",
        operation_id="attest",
        request=None,
        responses={
            HTTP_204_NO_CONTENT: ExpensePartSerializer,
            HTTP_403_FORBIDDEN: problems(AttestationPermissionDenied),
        },
    )
    def post(self, request, pk: int):
        expense_part = self.get_object()

        with transaction.atomic():
            expense_part = ExpensePart.objects.select_for_update().get(pk=pk)
            try:
                expense_part.attest(self.current_user)
            except UnauthorizedAttestationError:
                raise AttestationPermissionDenied(
                    detail=f"You do not have permission to attest this expense part, {expense_part.cost_centre} is not a cost centre for which you can attest."
                )
            except SelfAttestationError:
                raise AttestationPermissionDenied(
                    detail="You do not have permission to attest this expense part, you cannot attest for your own expenses."
                )

        return Response(
            ExpensePartSerializer(expense_part).data, status=status.HTTP_204_NO_CONTENT
        )
