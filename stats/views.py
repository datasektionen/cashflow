from datetime import datetime

from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, Coalesce
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings

import json

from expenses import models


def index(request):
    year = models.Expense.objects \
        .filter(expense_date__year=datetime.now().year, reimbursement__isnull=False) \
        .aggregate(sum=Coalesce(Sum('expensepart__amount'), 0))['sum']

    highscore = models.Profile.objects \
        .filter(expense__reimbursement__isnull=False, expense__expensepart__amount__lt=10000) \
        .annotate(total_amount=Sum('expense__expensepart__amount')) \
        .annotate(receipts=Count('expense__expensepart')) \
        .filter(total_amount__gte=0)

    highscore_amount = highscore.order_by('-total_amount')[:10]
    highscore_receipts = highscore.order_by('-receipts', '-total_amount')[:10]

    month_year = datetime.now().year
    month_count, month_sum = monthly_chart_data(month_year)

    return render(request, 'stats/index.html', {
        'year': year,
        'highscore_amount': highscore_amount,
        'highscore_receipts': highscore_receipts,
        'month_year': month_year,
        'month_count': month_count,
        'month_sum': month_sum,
        'month_count_total': sum(month_count),
        'month_sum_total': str(sum(month_sum)), # prevent django from formatting decimal as , in JS
        'budget_url': settings.BUDGET_URL,
    })

@csrf_exempt
def summary(request):
    if request.method == "POST":
        body_data = json.loads(request.body)
        # we tried getting it to work with ids, but it didn't,
        # so we're using names for now

        expense_parts = None

        if "year" in body_data:
             expense_parts = models.ExpensePart.objects.filter(
                 budget_line_name=body_data['budget_line'],
                 cost_centre=body_data['cost_centre'],
                 secondary_cost_centre=body_data['cost_centre'],
                 expense__expense_date__year=body_data['year'],
            ).all()
        else:
            expense_parts = models.ExpensePart.objects.filter(
                budget_line_name=body_data['budget_line'],
                cost_centre=body_data['cost_centre'],
                secondary_cost_centre=body_data['cost_centre'],
            ).all()

        sum_amount = 0

        for expense_part in expense_parts:
            sum_amount += expense_part.amount

        return JsonResponse({
            'name': body_data['cost_centre'],
            'costCentre': body_data['cost_centre'],
            'budgetLine': body_data['budget_line'],
            'year': body_data.get("year"),
            'amount': sum_amount,
        })
    return Response(status=status.HTTP_404_NOT_FOUND)


@require_GET
def monthly(_request, year):
    try:
        year = int(year)
        month_count, month_sum = monthly_chart_data(year)
        
        return JsonResponse({
                'year': year,
                'month_count': month_count,
                'month_sum': month_sum,
        })
    except ValueError:
        return HttpResponseBadRequest


def monthly_chart_data(year):
    if not isinstance(year, int) or year < 2000 or year > 3000:
        raise ValueError

    months = models.Expense.objects.filter(expense_date__year=year) \
        .annotate(date=TruncMonth('expense_date')) \
        .values('date') \
        .annotate(count=Count('id', distinct=True), sum=Sum('expensepart__amount')) \
        .order_by('date') \
        .all()

    months = [months.filter(date__month=i) for i in range(1, 13)]

    values = [
        (0, 0) if m.count() == 0 else (m.get()['count'], float(m.get()['sum']))
        for m in months
    ]
    return [list(v) for v in zip(*values)]
