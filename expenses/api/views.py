"""
API views for expense management.

This module contains all REST API endpoints related to expenses, including
creating, retrieving, updating, and deleting expense records. Each view
handles HTTP request validation, permission checks, and returns JSON responses.

New endpoints should be registered in api/urls.py and follow the existing
patterns for authentication and error handling found in this file.
"""

import json
from enum import Enum

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers, status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.response import Response
from structlog import get_logger

from expenses.models import Expense, ExpensePart, File, Profile

UserModel = get_user_model()

logger = get_logger(__name__)


class Filter(str, Enum):
    USER = "user"
    COST_CENTER = "cost_center"


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = "__all__"


class ProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")

    class Meta:
        model = Profile
        fields = [
            "id",
            "first_name",
            "last_name",
        ]


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


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        assert isinstance(user, User)

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
            expense = serializer.save(owner=user.profile)
            for f in files:
                File.objects.create(expense=expense, file=f)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        user = self.request.user
        assert isinstance(user, User)

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

        return Expense.objects.viewable_by(user).filter(**filter_map).distinct()


class ExpensePartViewSet(viewsets.ModelViewSet):
    serializer_class = ExpensePartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        assert isinstance(user, User)

        return ExpensePart.objects.filter(expense__in=Expense.objects.viewable_by(user))
