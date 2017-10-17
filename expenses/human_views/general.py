from django.shortcuts import render
from django.db import connection
from expenses import models

def index(request):
    return render(request, 'expenses/main.html')

def budget(request):
    with connection.cursor() as cursor:
        cursor.execute('''SELECT expenses_committee.id, expenses_committee.name AS committee_name, expenses_costcentre.id, expenses_costcentre.name AS costcentre_name, expenses_budgetline.id, expenses_budgetline.name AS budgetline_name, SUM(amount) as spent 
            FROM expenses_committee
            LEFT JOIN expenses_costcentre 
                ON expenses_costcentre.committee_id = expenses_committee.id 
            LEFT JOIN expenses_budgetline 
                ON expenses_budgetline.cost_centre_id = expenses_costcentre.id 
            LEFT JOIN expenses_expensepart 
                ON expenses_expensepart.budget_line_id = expenses_budgetline.id 
            GROUP BY expenses_committee.id, expenses_committee.name, expenses_costcentre.id, expenses_costcentre.name, expenses_budgetline.id, expenses_budgetline.name
            ORDER BY expenses_committee.name, expenses_costcentre.name, expenses_budgetline.name''')
        columns = [col[0] for col in cursor.description]
        return render(request, 'expenses/budget_overview.html', {
            'columns': columns,
            'expenses': (dict(zip(columns, row)) for row in cursor.fetchall())
        })
