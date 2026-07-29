from datetime import date
from decimal import Decimal
from enum import Enum

from django.db.models import QuerySet, Q, Subquery, Value
from django.db.models.aggregates import Sum, Count
from django.db.models.functions import Coalesce
from rest_framework import serializers
from rest_framework.generics import ListAPIView

from core.api.pagination import DefaultPagination
from core.api.serializers import ProfileSerializer
from expenses.models import Expense, Profile


class LeaderboardFilter(str, Enum):
    START_DATE = "start_date"
    END_DATE = "end_date"


class LeaderboardSerializer(serializers.Serializer):
    owner = ProfileSerializer(source="*", read_only=True)
    expense_total = serializers.DecimalField(
        max_digits=11, decimal_places=2, read_only=True
    )
    expense_count = serializers.IntegerField(read_only=True)


class LeaderboardQuerySerializer(serializers.Serializer):
    ORDERING_FIELDS = {"expense_total", "expense_count"}

    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    ordering = serializers.CharField(required=False)

    def validate_ordering(self, value):
        if value.lstrip("-") not in self.ORDERING_FIELDS:
            raise serializers.ValidationError(
                f"ordering must be one of {sorted(self.ORDERING_FIELDS)}, "
                "optionally prefixed with '-' for descending order."
            )
        return value

    def validate(self, attrs):
        start = attrs.get(LeaderboardFilter.START_DATE)
        end = attrs.get(LeaderboardFilter.END_DATE)
        if start and end and end < start:
            raise serializers.ValidationError(
                {LeaderboardFilter.END_DATE: "end_date must not be before start_date."}
            )
        return attrs


class StatisticsView(ListAPIView):
    serializer_class = LeaderboardSerializer
    pagination_class = DefaultPagination

    def get_queryset(self) -> QuerySet[Profile]:

        query = LeaderboardQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)

        start = query.validated_data.get(LeaderboardFilter.START_DATE) or date.min
        end = query.validated_data.get(LeaderboardFilter.END_DATE)
        ordering = query.validated_data.get("ordering") or "-expense_total"

        included = Q(
            expense__expense_date__gte=start,
        )
        if end is not None:
            included &= Q(expense__expense_date__lte=end)

        capped_expenses = (
            Expense.objects.filter(
                expense_date__gte=start,
            )
            .annotate(part_total=Sum("expensepart__amount"))
            .filter(part_total__lt=10000)
        )
        if end is not None:
            capped_expenses = capped_expenses.filter(expense_date__lte=end)

        total_included = Q(expense__in=Subquery(capped_expenses.values("pk")))

        queryset = (
            Profile.objects.annotate(
                expense_total=Coalesce(
                    Sum("expense__expensepart__amount", filter=total_included),
                    Value(Decimal("0.00")),
                )
            )
            .annotate(expense_count=Count("expense", filter=included, distinct=True))
            .filter(expense_count__gt=0)
            .order_by(ordering, "-expense_total", "-expense_count")
        )

        return queryset
