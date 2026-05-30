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
from rest_framework import serializers, status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.response import Response
from structlog import get_logger

from core.api.filters import Filter
from core.api.serializers import FileSerializer, ProfileSerializer
from core.api.utils import AuthenticatedUserMixin
from expenses.models import Expense, ExpensePart, File

UserModel = get_user_model()

logger = get_logger(__name__)


class ExpensePartSerializer(serializers.ModelSerializer):
    expense: PrimaryKeyRelatedField[Expense] = PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ExpensePart
        fields = [
            "expense",
            "cost_centre",
            "secondary_cost_centre",
            "budget_line",
            "amount",
        ]


class ExpenseSerializer(serializers.ModelSerializer):
    files = FileSerializer(many=True, source="file_set", read_only=True)
    owner = ProfileSerializer(read_only=True)
    parts = ExpensePartSerializer(many=True, required=True, allow_empty=False)

    class Meta:
        model = Expense
        fields = "__all__"

    def create(self, validated_data):
        parts_data = validated_data.pop("parts", [])
        expense = Expense.objects.create(**validated_data)
        for part in parts_data:
            ExpensePart.objects.create(expense=expense, **part)
        return expense


@extend_schema_view(
    list=extend_schema(
        summary="List expenses",
        description=(
            "Returns the paginated set of expenses the requesting user is "
            "allowed to see. Supports optional filtering by owner via "
            "`?user=<username>` and by cost centre via `?cost_center=<name>`."
        ),
        operation_id="list_expenses",
        tags=["Expenses"],
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
        description=(
            "Creates an expense together with its parts and one or more "
            "attached receipt files. Submit as `multipart/form-data` with "
            "the `parts` field as a JSON-encoded array; at least one file "
            "is required."
        ),
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
)
class ExpenseViewSet(viewsets.ModelViewSet, AuthenticatedUserMixin):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        files = request.FILES.getlist("files")
        if not files:
            raise serializers.ValidationError(
                {"files": "At least one file is required."}
            )

        data = (
            request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
        )
        if isinstance(data.get("parts"), str):
            try:
                data["parts"] = json.loads(data["parts"])
            except json.JSONDecodeError:
                raise serializers.ValidationError({"parts": "Must be valid JSON."})

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            expense = serializer.save(owner=self.current_user.profile)
            for f in files:
                File.objects.create(expense=expense, file=f)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
        )


class ExpensePartViewSet(viewsets.ModelViewSet, AuthenticatedUserMixin):
    serializer_class = ExpensePartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return ExpensePart.objects.filter(
            expense__in=Expense.objects.viewable_by(self.current_user)
        )
