from django.shortcuts import render
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from expenses import models

@require_http_methods(["GET", "POST"])
def new_invoice(request):
    if request.method == 'GET': return render(request, 'invoices/new.html')
    # Validate
    if len((request.FILES.getlist('files'))) < 1:
        messages.error(request, 'Du måste ladda upp minst en fil med fakturan')
        return HttpResponseRedirect(reverse('invoices-new'))

    if datetime.now() < datetime.strptime(request.POST['invoice-date'], '%Y-%m-%d'):
        messages.error(request, 'Du har angivit ett datum i framtiden som fakturadatum')
        return HttpResponseRedirect(reverse('invoices-new'))

    # Create the invoice
    invoice = models.Invoice(
        owner=request.user.profile,
        invoice_date=request.POST['invoice-date'],
        due_date=request.POST['due-date'],
        description=request.POST['expense-description'],
        confirmed_by=None
    )
    invoice.save()

    # Add the file
    for uploaded_file in request.FILES.getlist('files'):
        file = models.File(belonging_to=invoice, file=uploaded_file)
        file.save()

    # Add the expenseparts
    for idx, budgetLineId in enumerate(request.POST.getlist('budgetLine[]')):
        response = requests.get("https://budget.datasektionen.se/api/budget-lines/{}".format(budgetLineId))
        budgetLine = response.json()
        models.ExpensePart(
            expense=invoice,
            budget_line_id=budgetLine['id'],
            budget_line_name=budgetLine['name'],
            cost_centre_name=budgetLine['cost_centre']['name'],
            cost_centre_id=budgetLine['cost_centre']['id'],
            committee_name=budgetLine['cost_centre']['committee']['name'],
            committee_id=budgetLine['cost_centre']['committee']['id'],
            amount=request.POST.getlist('amount[]')[idx]
        ).save()

    return HttpResponseRedirect(reverse('invoices-new-confirmation', kwargs={'pk': expense.id}))