from django.shortcuts import render
from django.db import connection
from expenses import models
from django.db.models import Sum

"""
Simply renders main.html view.
"""
def index(request):
    return render(request, 'expenses/stats/index.html', {
        'year': models.Expense.objects.filter(reimbursement__isnull=False).aggregate(year=Sum('expensepart__amount'))['year'],
        'highscore': models.Profile.objects.filter(expense__reimbursement__isnull=False).annotate(
            total_amount=Sum('expense__expensepart__amount')
        ).filter(total_amount__gte=0).order_by('-total_amount')[:10]
    })