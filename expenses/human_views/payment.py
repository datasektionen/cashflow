from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import render

from expenses import models


def get_payment(request, pk):
    try:
        payment = models.Payment.objects.get(pk=pk)

        return render(request, 'expenses/payment.html', {
            'payment': payment
        })
    except ObjectDoesNotExist:
        return Http404("Utbetalningen finns inte")
