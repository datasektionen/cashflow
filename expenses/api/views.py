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
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from cashflow import dauth
from expenses.models import Expense

UserModel = get_user_model()


class Filter(str, Enum):
    USER = "user"
    COST_CENTER = "cost_center"


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = "__all__"


class ExpenseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

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
