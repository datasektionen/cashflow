"""
API views for expense management.

This module contains all REST API endpoints related to expenses, including
creating, retrieving, updating, and deleting expense records. Each view
handles HTTP request validation, permission checks, and returns JSON responses.

New endpoints should be registered in api/urls.py and follow the existing
patterns for authentication and error handling found in this file.
"""
from enum import Enum

from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers, status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cashflow import dauth
from expenses.models import Expense, File

UserModel = get_user_model()


class Filter(str, Enum):
    USER = "user"
    COST_CENTER = "cost_center"


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = "__all__"


class ExpenseSerializer(serializers.ModelSerializer):
    files = FileSerializer(many=True, source='file_set', read_only=True)
    owner = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Expense
        fields = "__all__"


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist('files')
        if not files:
            raise serializers.ValidationError({"files": "At least one file is required."})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expense = serializer.save(owner=request.user.profile)
        for f in files:
            File.objects.create(expense=expense, file=f)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):

        filter_map = {}
        if self.request.GET.get(Filter.USER):
            try:
                filtered_user = UserModel.objects.get(username=self.request.GET.get(Filter.USER))
                filter_map["owner__user"] = filtered_user
            except UserModel.DoesNotExist:
                pass
        if self.request.GET.get(Filter.COST_CENTER):
            filter_map["expensepart__cost_centre__in"] = [self.request.GET.get(Filter.COST_CENTER)]

        if dauth.has_scoped_permission(dauth.Permission.VIEW_EXPENSES, "*", self.request.user):
            # User may view all expenses
            return Expense.objects.filter(**filter_map).distinct()

        else:

            # Find all cost centers that user may view expenses for
            cc_scopes = dauth.get_permissions(self.request.user).get(dauth.Permission.VIEW_EXPENSES, [])

            # Q allows you to perform "OR" filtering. A user will have access to (1) their own expenses, OR (2)
            # expenses in a cost center for which they have permissions for
            base_query = Expense.objects.filter(
                Q(owner__user=self.request.user) | Q(expensepart__cost_centre__in=cc_scopes)).distinct()

            return base_query.filter(**filter_map)
