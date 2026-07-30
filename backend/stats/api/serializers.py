from enum import Enum

from rest_framework import serializers

from core.api.serializers import ProfileSerializer


class LeaderboardSerializer(serializers.Serializer):
    owner = ProfileSerializer(source="*", read_only=True)
    expense_total = serializers.DecimalField(
        max_digits=11, decimal_places=2, read_only=True
    )
    expense_count = serializers.IntegerField(read_only=True)


class LeaderboardQuerySerializer(serializers.Serializer):
    ORDERING_FIELDS = {"expense_total", "expense_count"}

    start_date = serializers.DateField(
        required=False,
        help_text="Only count expenses on or after this date (inclusive).",
    )
    end_date = serializers.DateField(
        required=False,
        help_text="Only count expenses on or before this date (inclusive).",
    )
    ordering = serializers.CharField(
        required=False,
        help_text=(
            "Field to order by: 'expense_total' (default) or 'expense_count'. "
            "Prefix with '-' for descending order."
        ),
    )

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


class MonthlyStatisticsSerializer(serializers.Serializer):
    year = serializers.IntegerField(read_only=True)
    month = serializers.IntegerField(read_only=True)
    expense_count = serializers.IntegerField(read_only=True)
    invoice_count = serializers.IntegerField(read_only=True)
    expense_total = serializers.DecimalField(
        max_digits=11, decimal_places=2, read_only=True
    )
    invoice_total = serializers.DecimalField(
        max_digits=11, decimal_places=2, read_only=True
    )


class YearlyStatisticsSerializer(serializers.Serializer):
    year = serializers.IntegerField(read_only=True)
    months = MonthlyStatisticsSerializer(many=True, read_only=True)


class LeaderboardFilter(str, Enum):
    START_DATE = "start_date"
    END_DATE = "end_date"
