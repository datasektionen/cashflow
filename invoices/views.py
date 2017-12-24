from django.shortcuts import render
from django.http import Http404, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseServerError, JsonResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import date, datetime
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

from expenses.models import *
from invoices.models import *

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
    invoice = Invoice(
        owner=request.user.profile,
        invoice_date=request.POST['invoice-date'],
        due_date=request.POST['invoice-due-date'],
        description=request.POST['invoice-description'],
        confirmed_by=None
    )
    invoice.save()

    # Add the file
    for uploaded_file in request.FILES.getlist('files'):
        file = File(invoice=invoice, file=uploaded_file)
        file.save()

    # Add the expenseparts
    for idx, budgetLineId in enumerate(request.POST.getlist('budgetLine[]')):
        response = requests.get("https://budget.datasektionen.se/api/budget-lines/{}".format(budgetLineId))
        budgetLine = response.json()
        InvoicePart(
            invoice=invoice,
            budget_line_id=budgetLine['id'],
            budget_line_name=budgetLine['name'],
            cost_centre_name=budgetLine['cost_centre']['name'],
            cost_centre_id=budgetLine['cost_centre']['id'],
            committee_name=budgetLine['cost_centre']['committee']['name'],
            committee_id=budgetLine['cost_centre']['committee']['id'],
            amount=request.POST.getlist('amount[]')[idx]
        ).save()

    return HttpResponseRedirect(reverse('invoices-new-confirmation', kwargs={'pk': invoice.id}))

"""
Shows a confirmation of the new invoice and tells user to put invoice into binder.
"""
@require_GET
@login_required
def invoice_new_confirmation(request, pk):
    try: invoice = Invoice.objects.get(pk=int(pk))
    except ObjectDoesNotExist:
        messages.error(request, 'Ett fel uppstod och kvittot skapades inte.')
        return HttpResponseRedirect(reverse('invoices-new'))

    return render(request, 'invoices/confirmation.html', {'invoice': invoice})



"""
Shows one expense.
"""
@require_GET
@login_required
def get_invoice(request, pk):
    try: invoice = Invoice.objects.get(pk=int(pk))
    except ObjectDoesNotExist: raise Http404("Utlägget finns inte")

    if not request.user.profile.may_view_invoice(invoice): return HttpResponseForbidden()

    return render(request, 'invoices/show.html', {
        'invoice': invoice,
        'may_account': request.user.profile.may_account()
    })



"""
Adds new comment to invoice.
"""
@require_POST
@login_required
def new_comment(request, invoice_pk):
    try: invoice = models.Invoice.objects.get(pk=int(invoice_pk))
    except ObjectDoesNotExist: raise Http404("Utlägget finns inte")

    if not request.user.profile.may_view_invoice(invoice): return HttpResponseForbidden()
    if re.match('^\s*$', request.POST['content']): return HttpResponseRedirect(reverse('invoices-show', kwargs={'pk': invoice_pk}))
    
    models.Comment(
        invoice=invoice,
        author=request.user.profile,
        content=request.POST['content']
    ).save()

    return HttpResponseRedirect(reverse('invoices-show', kwargs={'pk': invoice_pk}))

