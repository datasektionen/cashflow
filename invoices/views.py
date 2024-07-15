from django.shortcuts import render
from django.http import Http404, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseServerError, JsonResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from datetime import date, datetime
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from cashflow import settings
from cashflow import email

import re

from expenses.models import *
from invoices.models import *

@require_http_methods(["GET", "POST"])
def new_invoice(request):
    if request.method == 'GET':
        return render(request, 'invoices/new.html', {'budget_url': settings.BUDGET_URL})

    invdate = request.POST['invoice-date'] if re.match('[0-9]{4}-[0-9]{2}-[0-9]{2}', request.POST['invoice-date']) else None
    duedate = request.POST['invoice-due-date'] if re.match('[0-9]{4}-[0-9]{2}-[0-9]{2}', request.POST['invoice-due-date']) else None

    # Beneficial to not return per check, because then several errors can be reported at once
    valid = True
    
    if len((request.FILES.getlist('files'))) < 1:
        messages.error(request, 'Du måste ladda upp minst en fil med fakturan')
        valid = False

    if any(map(lambda x: float(x) <= 0, request.POST.getlist('amounts[]'))) > 0:
        messages.error(request, 'Du har angivit en icke-positiv summa i någon av fakturadelarna')
        valid = False

    if len(request.POST.getlist('budgetLines[]')) == 0:
        messages.error(request, 'Du måste lägga till minst en del på kvittot')
        valid = False

    if invdate > duedate:
        messages.error(request, 'Fakturadatumet är efter förfallodatumet')
        valid = False

    if not valid:
        return HttpResponseRedirect(reverse('invoices-new'))


    invoice = Invoice(
        owner=request.user.profile,
        invoice_date=invdate,
        due_date=duedate,
        file_is_original=(request.POST['invoice-original'] == "yes"),
        description=request.POST['invoice-description'],
    )
    invoice.save()

    if request.POST['payed'] != 'no-chapter-will':
        invoice.payed_by = request.user
        invoice.payed_at = date.today()
        if request.POST['accounted'] == 'accounted-yes':
            invoice.verification = request.POST['verification']
        invoice.save()


    # Add the file
    for uploaded_file in request.FILES.getlist('files'):
        file = File(invoice=invoice, file=uploaded_file)
        file.save()

    # Add the expenseparts
    for cost_centre, secondary_cost_centre, budget_line, amount in zip(
        request.POST.getlist("costCentres[]"),
        request.POST.getlist("secondaryCostCentres[]"),
        request.POST.getlist("budgetLines[]"),
        request.POST.getlist("amounts[]"),
    ):
        InvoicePart(
            invoice=invoice,
            cost_centre=cost_centre,
            secondary_cost_centre=secondary_cost_centre,
            budget_line=budget_line,
            amount=amount,
        ).save()

    return HttpResponseRedirect(reverse('invoices-new-confirmation', kwargs={'pk': invoice.id}))

"""
Shows a confirmation of the new invoice and tells user to put invoice into binder.
"""
@require_GET
@login_required
def invoice_new_confirmation(request, pk):
    try:
        invoice = Invoice.objects.get(pk=int(pk))

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

    attestable = []
    for invoice_part in invoice.invoicepart_set.all():
        if request.user.profile.may_attest(invoice_part):
            attestable.append(invoice_part.id)

    return render(request, 'invoices/show.html', {
        'invoice': invoice,
        'attestable': attestable,
        'may_account': request.user.profile.may_account(),
        'budget_url': settings.BUDGET_URL,
    })



"""
Adds new comment to invoice.
"""
@require_POST
@login_required
def new_comment(request, invoice_pk):
    try: invoice = Invoice.objects.get(pk=int(invoice_pk))
    except ObjectDoesNotExist: raise Http404("Utlägget finns inte")

    if not request.user.profile.may_view_invoice(invoice): return HttpResponseForbidden()
    if re.match('^\s*$', request.POST['content']): return HttpResponseRedirect(reverse('invoices-show', kwargs={'pk': invoice_pk}))
    
    Comment(
        invoice=invoice,
        author=request.user.profile,
        content=request.POST['content']
    ).save()

    return HttpResponseRedirect(reverse('invoices-show', kwargs={'pk': invoice_pk}))

@require_http_methods(["GET", "POST"])
@login_required
def delete_invoice(request, pk):
    """
    Delete invoice. Ask for confirmation on GET and send to POST.
    """
    try:
        invoice = Invoice.objects.get(pk=pk)
    except ObjectDoesNotExist:
        raise Http404("Fakturan finns inte")

    may_delete_invoice = request.user.profile.may_delete_invoice(invoice)

    if request.method == 'GET':
        return render(request, 'invoices/delete.html', {'invoice': invoice, 'may_delete': may_delete_invoice})
    if request.method == 'POST':
        if not may_delete_invoice:
            return HttpResponseForbidden('Du har inte behörighet att ta bort denna faktura.')
        invoice.delete()
        # Inform owner that someone removed it
        if request.user != invoice.owner.user:
            receiver_name = invoice.owner.user.first_name + ' ' + invoice.owner.user.last_name
            deleter_name = request.user.first_name + ' ' + request.user.last_name
            recipient = invoice.owner.user.email
            subject = deleter_name + ' har tagit bort din faktura'
            content = render_to_string("remove_invoice_email.html", {'deleter': deleter_name, 'receiver': receiver_name, 'description': invoice.description})
            email.send_mail(recipient, subject, content)
        return HttpResponseRedirect(reverse('expenses-index'))
