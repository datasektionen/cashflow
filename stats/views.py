from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, Coalesce
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_GET

from expenses import models


def index(request):
    year = models.Expense.objects.filter(
        expense_date__year=datetime.now().year, reimbursement__isnull=False
    ).aggregate(sum=Coalesce(Sum("expensepart__amount"), Decimal(0)))["sum"]

    highscore = (
        models.Profile.objects.filter(
            expense__reimbursement__isnull=False, expense__expensepart__amount__lt=10000
        )
        .annotate(total_amount=Sum("expense__expensepart__amount"))
        .annotate(receipts=Count("expense__expensepart"))
        .filter(total_amount__gte=0)
    )

    highscore_amount = highscore.order_by("-total_amount")[:10]
    highscore_receipts = highscore.order_by("-receipts", "-total_amount")[:10]

    month_year = datetime.now().year
    month_count, month_sum = monthly_chart_data(month_year)

    return render(
        request,
        "stats/index.html",
        {
            "year": year,
            "highscore_amount": highscore_amount,
            "highscore_receipts": highscore_receipts,
            "month_year": month_year,
            "month_count": month_count,
            "month_sum": month_sum,
            "month_count_total": sum(month_count),
            "month_sum_total": str(sum(month_sum)),
            # prevent django from formatting decimal as , in JS
            "budget_url": settings.BUDGET_URL,
        },
    )


@require_GET
def summary(request):
    expense_parts = None

    cost_centre = request.GET.get("cost_centre")
    year = request.GET.get("year")
    secondary_cost_centre = request.GET.get("secondary_cost_centre")
    budget_line = request.GET.get("budget_line")

    if not cost_centre or not year:
        return JsonResponse({"error": "cost_centre and year are required"}, status=400)
    if secondary_cost_centre == "":
        expense_parts = models.ExpensePart.objects.filter(
            cost_centre=cost_centre, expense__expense_date__year=year
        ).all()
    elif budget_line == "":
        expense_parts = models.ExpensePart.objects.filter(
            cost_centre=cost_centre,
            expense__expense_date__year=year,
            secondary_cost_centre=secondary_cost_centre,
        ).all()
    else:
        expense_parts = models.ExpensePart.objects.filter(
            cost_centre=cost_centre,
            expense__expense_date__year=year,
            secondary_cost_centre=secondary_cost_centre,
            budget_line=budget_line,
        ).all()

    sum_amount = 0
    for expense_part in expense_parts:
        sum_amount += expense_part.amount

    return JsonResponse({"amount": sum_amount})


@require_GET
def sec_cost_centres(request):
    cost_centre = request.GET.get("cost_centre")
    year = request.GET.get("year")
    if not cost_centre or not year:
        return JsonResponse({"error": "cost_centre and year are required"}, status=400)

    expense_parts = models.ExpensePart.objects.filter(
        cost_centre=cost_centre, expense__expense_date__year=year
    ).all()

    sec_cost_centres = set()
    for expense_part in expense_parts:
        sec_cost_centres.add(expense_part.secondary_cost_centre)

    return JsonResponse({"sec_cost_centres": list(sec_cost_centres)})


@require_GET
def budget_lines(request):
    cost_centre = request.GET.get("cost_centre")
    year = request.GET.get("year")
    secondary_cost_centre = request.GET.get("secondary_cost_centre")
    if not cost_centre or not year or not secondary_cost_centre:
        return JsonResponse({"error": "cost_centre and year are required"}, status=400)

    expense_parts = models.ExpensePart.objects.filter(
        cost_centre=cost_centre,
        expense__expense_date__year=year,
        secondary_cost_centre=secondary_cost_centre,
    ).all()

    budget_lines = set()
    for expense_part in expense_parts:
        budget_lines.add(expense_part.budget_line)

    return JsonResponse({"budget_lines": list(budget_lines)})


@require_GET
def cost_centres(request):
    """
    Returns the distinct cost centres (committees) from all expenses.
    """
    cost_centres = set()
    for expense in models.Expense.objects.all():
        for cost_centre in expense.cost_centres():
            cost_centres.add(cost_centre["cost_centre"])

    return JsonResponse({"cost_centres": list(cost_centres)})


@require_GET
def monthly(_request, year):
    try:
        year = int(year)
        month_count, month_sum = monthly_chart_data(year)

        return JsonResponse(
            {
                "year": year,
                "month_count": month_count,
                "month_sum": month_sum,
            }
        )
    except ValueError:
        return HttpResponseBadRequest


def monthly_chart_data(year):
    if not isinstance(year, int) or year < 2000 or year > 3000:
        raise ValueError

    months = (
        models.Expense.objects.filter(expense_date__year=year)
        .annotate(date=TruncMonth("expense_date"))
        .values("date")
        .annotate(count=Count("id", distinct=True), sum=Sum("expensepart__amount"))
        .order_by("date")
        .all()
    )

    months = [months.filter(date__month=i) for i in range(1, 13)]

    values = [
        (0, 0) if m.count() == 0 else (m.get()["count"], float(m.get()["sum"]))
        for m in months
    ]
    return [list(v) for v in zip(*values)]
