from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Q, Subquery, Value
from django.db.models.aggregates import Count, Sum
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.pagination import DefaultPagination
from core.models import Claim, Profile
from stats.api.serializers import (
    LeaderboardFilter,
    LeaderboardQuerySerializer,
    LeaderboardSerializer,
    MonthlyStatisticsSerializer,
    YearlyStatisticsSerializer,
)


class LeaderboardView(ListAPIView):
    serializer_class = LeaderboardSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):

        query = LeaderboardQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)

        start = query.validated_data.get(LeaderboardFilter.START_DATE) or date.min
        end = query.validated_data.get(LeaderboardFilter.END_DATE)
        ordering = query.validated_data.get("ordering") or "-expense_total"

        included = Q(
            claim__expense_data__expense_date__gte=start,
        )
        if end is not None:
            included &= Q(claim__expense_data__expense_date__lte=end)

        capped_expenses = (
            Claim.objects.expenses()
            .filter(
                expense_data__expense_date__gte=start,
            )
            .annotate(part_total=Sum("part__amount"))
            .filter(part_total__lt=10000)
        )
        if end is not None:
            capped_expenses = capped_expenses.filter(
                expense_data__expense_date__lte=end
            )

        total_included = Q(claim__in=Subquery(capped_expenses.values("pk")))

        queryset = (
            Profile.objects.annotate(
                expense_total=Coalesce(
                    Sum("claim__part__amount", filter=total_included),
                    Value(Decimal("0.00")),
                )
            )
            .annotate(expense_count=Count("claim", filter=included, distinct=True))
            .filter(expense_count__gt=0)
            .order_by(ordering, "-expense_total", "-expense_count")
        )

        return queryset


class MonthlyStatisticsView(APIView):
    def get(
        self, request, year: int | None = None, month: int | None = None
    ) -> Response:

        year = year or timezone.localdate().year
        month = month or timezone.localdate().month

        start_date = date(year, month, 1)
        end_date = start_date + relativedelta(months=1)

        expense_stats = Claim.objects.filter(
            expense_data__expense_date__gte=start_date,
            expense_data__expense_date__lt=end_date,
        ).aggregate(
            count=Count("pk", distinct=True),
            total=Coalesce(Sum("part__amount"), Value(Decimal("0.00"))),
        )

        invoice_stats = Claim.objects.filter(
            invoice_data__invoice_date__gte=start_date,
            invoice_data__invoice_date__lt=end_date,
        ).aggregate(
            count=Count("pk", distinct=True),
            total=Coalesce(Sum("part__amount"), Value(Decimal("0.00"))),
        )

        data = {
            "year": year,
            "month": month,
            "expense_count": expense_stats["count"],
            "invoice_count": invoice_stats["count"],
            "expense_total": expense_stats["total"],
            "invoice_total": invoice_stats["total"],
        }

        return Response(MonthlyStatisticsSerializer(data).data)


def _empty_month_stats(year: int, month: int) -> dict:
    return {
        "year": year,
        "month": month,
        "expense_count": 0,
        "invoice_count": 0,
        "expense_total": Decimal("0.00"),
        "invoice_total": Decimal("0.00"),
    }


class YearlyStatisticsView(APIView):
    def get(self, request, year: int | None = None) -> Response:

        year = year or timezone.localdate().year

        year_start = date(year, 1, 1)
        year_end = year_start + relativedelta(years=1)

        months = {month: _empty_month_stats(year, month) for month in range(1, 13)}

        expense_rows = (
            Claim.objects.filter(
                expense_data__expense_date__gte=year_start,
                expense_data__expense_date__lt=year_end,
            )
            .annotate(period=TruncMonth("expense_data__expense_date"))
            .values("period")
            .annotate(
                count=Count("pk", distinct=True),
                total=Coalesce(Sum("part__amount"), Value(Decimal("0.00"))),
            )
        )
        for row in expense_rows:
            stats = months[row["period"].month]
            stats["expense_count"] = row["count"]
            stats["expense_total"] = row["total"]

        invoice_rows = (
            Claim.objects.filter(
                invoice_data__invoice_date__gte=year_start,
                invoice_data__invoice_date__lt=year_end,
            )
            .annotate(period=TruncMonth("invoice_data__invoice_date"))
            .values("period")
            .annotate(
                count=Count("pk", distinct=True),
                total=Coalesce(Sum("part__amount"), Value(Decimal("0.00"))),
            )
        )
        for row in invoice_rows:
            stats = months[row["period"].month]
            stats["invoice_count"] = row["count"]
            stats["invoice_total"] = row["total"]

        data = {
            "year": year,
            "months": [months[month] for month in range(1, 13)],
        }

        return Response(YearlyStatisticsSerializer(data).data)
