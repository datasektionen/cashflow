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

@require_GET
def summary(request):
    expense_parts = None

    cost_centre = request.GET.get('cost_centre')
    year = request.GET.get('year')
    secondary_cost_centre = request.GET.get('secondary_cost_centre')
    budget_line = request.GET.get('budget_line')

    if not cost_centre or not year:
        return JsonResponse({'error': 'cost_centre and year are required'}, status=400)
    if secondary_cost_centre == '':
        # Filter ExpensePart by cost_centre and year
        expense_parts = models.ExpensePart.objects.filter(
            cost_centre=cost_centre,
            expense__expense_date__year=year
        ).all()
    elif budget_line == '':
        # Filter ExpensePart by cost_centre and year
        expense_parts = models.ExpensePart.objects.filter(
            cost_centre=cost_centre,
            expense__expense_date__year=year,
            secondary_cost_centre=secondary_cost_centre
        ).all()
    else:
        # Filter ExpensePart by cost_centre and year
        expense_parts = models.ExpensePart.objects.filter(
            cost_centre=cost_centre,
            expense__expense_date__year=year,
            secondary_cost_centre=secondary_cost_centre,
            budget_line = budget_line
        ).all()

    sum_amount = 0
    expense_parts_list = []  # To store each expense part for debugging or detailed view

    for expense_part in expense_parts:
        sum_amount += expense_part.amount
        # Optionally add the expense part details to the response
        expense_parts_list.append({
            'expense': str(expense_part.expense),  # String representation of the expense
            'amount': float(expense_part.amount),  # Convert to float for JSON compatibility
            'budget_line': expense_part.budget_line
        })

    return JsonResponse({
        'amount': sum_amount,
    })


@require_GET
def sec_cost_centres(request):
    expense_parts = None

    cost_centre = request.GET.get('cost_centre')
    year = request.GET.get('year')
    if not cost_centre or not year:
        return JsonResponse({'error': 'cost_centre and year are required'}, status=400)

    # Filter ExpensePart by cost_centre and year
    expense_parts = models.ExpensePart.objects.filter(
        cost_centre=cost_centre,
        expense__expense_date__year=year
    ).all()
    
    sec_cost_centres = set()

    for expense_part in expense_parts:
        sec_cost_centres.add(expense_part.secondary_cost_centre)
        # Optionally add the expense part details to the response

    sec_cost_centres_list = list(sec_cost_centres)

    return JsonResponse({
        'sec_cost_centres': sec_cost_centres_list
    })

@require_GET
def budget_lines(request):
    expense_parts = None

    cost_centre = request.GET.get('cost_centre')
    year = request.GET.get('year')
    secondary_cost_centre = request.GET.get('secondary_cost_centre')
    if not cost_centre or not year or not secondary_cost_centre:
        return JsonResponse({'error': 'cost_centre and year are required'}, status=400)

    # Filter ExpensePart by cost_centre and year
    expense_parts = models.ExpensePart.objects.filter(
        cost_centre=cost_centre,
        expense__expense_date__year=year,
        secondary_cost_centre = secondary_cost_centre
    ).all()
    
    budget_lines = set()

    for expense_part in expense_parts:
        budget_lines.add(expense_part.budget_line)

    budget_lines_list = list(budget_lines)

    return JsonResponse({
        'budget_lines': budget_lines_list
    })



@require_GET
def cost_centres(request):
    """
    Returns the distinct cost centres (committees) from all expenses.
    """
    year = request.GET.get('year')
    if not year:
        return JsonResponse({'error': 'year is required'}, status=400)

    # filter ExpensePart by year
    expense_parts = models.ExpensePart.objects.filter(
        expense__expense_date__year=year
    ).all()

    cost_centres = set() 

    for expense_part in expense_parts:
        cost_centres.add(expense_part.cost_centre)

    cost_centres_list = list(cost_centres)

    return JsonResponse({
        'cost_centres': cost_centres_list
    })



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
