import json
import re

from django.core.exceptions import ObjectDoesNotExist
from django.forms import modelform_factory
from django.http import Http404, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.db.models import Sum

from cashflow import dauth
from budget import models as budgetModels
from expenses import models

def budget_overview(request):
    if request.method == 'GET':
        committees = {}
        for committee in budgetModels.Committee.objects.order_by('name'):
            committees[committee.id] = {
                'name': committee.name,
                'cost_centres': {}
            }

            for cost_centre in budgetModels.CostCentre.objects.order_by('name'):
                committees[committee.id]['cost_centres'][cost_centre.id] = {
                    'name': cost_centre.name,
                    'budget_lines': {}
                }

                for budget_line in budgetModels.BudgetLine.objects.order_by('name'):
                    committees[committee.id]['cost_centres'][cost_centre.id]['budget_lines'][budget_line.id] = {
                        'name': budget_line.name,
                        'amount': float(budget_line.amount),
                        'spent': float(models.ExpensePart.objects.filter(budget_line=budget_line.id).aggregate(Sum('amount'))['amount__sum'] or 0)
                    }

        if len(dauth.get_permissions(request.user)) > 0:
            return render(request, 'budget/overview.html', {
                'committees': committees
            })
    else:
        raise Http404()
