from datetime import date, datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Q, Subquery, Value
from django.db.models.aggregates import Sum, Count
from django.db.models.functions import Coalesce, TruncMonth
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.pagination import DefaultPagination
from expenses.models import Expense, Profile
from invoices.models import Invoice
from stats.api.serializers import (
    LeaderboardSerializer,
    LeaderboardQuerySerializer,
    MonthlyStatisticsSerializer,
    YearlyStatisticsSerializer,
    LeaderboardFilter,
)


@extend_schema(
    tags=[
        "Statistics",
    ],
    summary="List leaderboard",
    parameters=[LeaderboardQuerySerializer],
    description="Lists users and their expense count and total sum of expenses, ordered by expense total (descending, default) or expense count.",
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


@extend_schema(
    tags=[
        "Statistics",
    ],
    summary="Monthly statistics",
    description="Retrieve statistics for one month.",
    responses=MonthlyStatisticsSerializer,
)
class MonthlyStatisticsView(APIView):

    def get(
        self, request, year: int | None = None, month: int | None = None
    ) -> Response:

        year = year or datetime.now().year
        month = month or datetime.now().month

        start_date = datetime(year, month, 1)
        end_date = start_date + relativedelta(months=1)

        expense_stats = Expense.objects.filter(
            expense_date__gte=start_date,
            expense_date__lt=end_date,
        ).aggregate(
            count=Count("pk", distinct=True),
            total=Coalesce(Sum("expensepart__amount"), Value(Decimal("0.00"))),
        )

        invoice_stats = Invoice.objects.filter(
            invoice_date__gte=start_date,
            invoice_date__lt=end_date,
        ).aggregate(
            count=Count("pk", distinct=True),
            total=Coalesce(Sum("invoicepart__amount"), Value(Decimal("0.00"))),
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


@extend_schema(
    tags=[
        "Statistics",
    ],
    summary="Yearly statistics",
    description="Retrieve statistics for each month of one year.",
    responses=YearlyStatisticsSerializer,
)
class YearlyStatisticsView(APIView):

    def get(self, request, year: int | None = None) -> Response:

        year = year or datetime.now().year

        year_start = datetime(year, 1, 1)
        year_end = year_start + relativedelta(years=1)

        months = {month: _empty_month_stats(year, month) for month in range(1, 13)}

        expense_rows = (
            Expense.objects.filter(
                expense_date__gte=year_start,
                expense_date__lt=year_end,
            )
            .annotate(period=TruncMonth("expense_date"))
            .values("period")
            .annotate(
                count=Count("pk", distinct=True),
                total=Coalesce(Sum("expensepart__amount"), Value(Decimal("0.00"))),
            )
        )
        for row in expense_rows:
            stats = months[row["period"].month]
            stats["expense_count"] = row["count"]
            stats["expense_total"] = row["total"]

        invoice_rows = (
            Invoice.objects.filter(
                invoice_date__gte=year_start,
                invoice_date__lt=year_end,
            )
            .annotate(period=TruncMonth("invoice_date"))
            .values("period")
            .annotate(
                count=Count("pk", distinct=True),
                total=Coalesce(Sum("invoicepart__amount"), Value(Decimal("0.00"))),
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
