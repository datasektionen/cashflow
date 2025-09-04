from django.shortcuts import render
from django.http import Http404, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseServerError, JsonResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import date, datetime
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
from pi_heif import register_heif_opener
from io import BytesIO

import re

from expenses.models import File
from expenses.models import Expense
from invoices.models import Invoice

register_heif_opener()

def pretty_request(request):
    headers = ''
    for header, value in request.META.items():
        if not header.startswith('HTTP'):
            continue
        header = '-'.join([h.capitalize() for h in header[5:].lower().split('_')])
        headers += '{}: {}\n'.format(header, value)

    return (
        '{method} HTTP/1.1\n'
        'Content-Length: {content_length}\n'
        'Content-Type: {content_type}\n'
        '{headers}\n\n'
        #'{body}'
    ).format(
        method=request.method,
        content_length=request.META['CONTENT_LENGTH'],
        content_type=request.META['CONTENT_TYPE'],
        headers=headers,
        #body=request.body,
    )


@require_http_methods(["POST"])
@csrf_exempt
def new_file(request):
    expense = None
    eId = request.GET.get('expense')
    if eId != None:
        expense = Expense.objects.get(pk=int(eId))
        expense.confirmed_by = None
        expense.confirmed_at = None
        expense.save()
    invoice = None
    iId = request.GET.get('invoice')
    if iId != None:
        if eId != None:
            return JsonResponse({'message':'Kan ej ange både expense och invoice'}, status=403)
        invoice = Invoice.objects.get(pk=int(iId))
        invoice.confirmed_by = None
        invoice.confirmed_at = None
        invoice.save()

    uploaded_file = request.FILES["file"]
    if uploaded_file.content_type in ['image/heif', 'image/heic']:
        img = BytesIO()
        with Image.open(uploaded_file) as im:
            im.save(img, format="jpeg")
        uploaded_file = InMemoryUploadedFile(
            img,
            None,
            uploaded_file.name.lower().replace(".heic", ".jpeg"),
            "image/jpeg",
            img.getbuffer().nbytes,
            "binary"
        )

    file = File(file=uploaded_file, expense=expense, invoice=invoice)
    file.save()

    return JsonResponse({"message": "File uploaded", "file": file.to_dict()})

@require_http_methods(["POST"])
@csrf_exempt
def delete_file(request, pk):
    file = File.objects.get(pk=int(pk))

    if file.expense != None:
        if not request.user.profile.may_delete_expense(file.expense):
            return JsonResponse({'message':'Du har inte behörighet att ta bort denna bild.'}, status=403)
        file.expense.confirmed_by = None
        file.expense.confirmed_at = None
        file.expense = None
    elif file.invoice != None:
        if not request.user.profile.may_delete_invoice(file.invoice):
            return JsonResponse({'message':'Du har inte behörighet att ta bort denna bild.'}, status=403)
        file.invoice.confirmed_by = None
        file.invoice.confirmed_at = None
        file.invoice = None
    else:
        return JsonResponse({'message':'Not found'}, status=404)
    file.save()

    return JsonResponse({'message':'File deleted.'})
