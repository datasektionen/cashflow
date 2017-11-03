from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.core import serializers
from django.forms.models import model_to_dict
from datetime import date, datetime
from decimal import *
import json

from cashflow import dauth
from expenses import models


def attest_overview(request):
    may_attest = request.user.profile.may_attest()
    print(may_attest)
    return render(request, 'expenses/action_attest.html', {
        'attestable_expenses': models.Expense.objects.exclude(owner__user=request.user).filter(
            expensepart__attested_by=None,
            expensepart__committee_name__iregex=r'(' + '|'.join(may_attest) + ')'
        ).distinct()
    })


def pay_overview(request):
    if not dauth.has_permission('pay', request):
        return HttpResponseForbidden("Du har inte rättigheterna för att se den här sidan")

    context = {
        'payable_expenses': models.Expense.objects.filter(reimbursement=None)
            .exclude(expensepart__attested_by=None).order_by('owner__user__username'),
        'accounts': models.BankAccount.objects.all().order_by('name')}

    if request.GET:
        context['payment'] = models.Payment.objects.get(id=int(request.GET['payment']))

    return render(request, 'expenses/action_pay.html', context)


def accounting_overview(request):
    may_account = request.user.profile.may_account()
    expenses = models.Expense.objects.exclude(reimbursement=None).filter(
        verification="",
        expensepart__committee_name__iregex=r'(' + '|'.join(may_account) + ')'
    ).distinct()

    class fakefloat(float):
        def __init__(self, value):
            self._value = value
        def __repr__(self):
            return str(self._value)

    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return fakefloat(obj)
        raise TypeError ("Type %s not serializable" % type(obj))


    return render(request, 'expenses/action_accounting.html', {
        'accounting_ready_expenses': json.dumps([expense.to_dict() for expense in expenses], default=json_serial)
    })
