from django.shortcuts import render

# Create your views here.
def new_invoice(request):
    return render(request, 'invoices/new.html', {
    })