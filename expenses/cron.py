import threading

import requests
from django.core.exceptions import ObjectDoesNotExist

from .models import Committee, CostCentre, BudgetLine


def start():
    threading.Timer(10, build_budget_from_api).start()  # Run first call after 10 seconds (let server start first)


def build_budget_from_api():
    threading.Timer(60 * 15, build_budget_from_api).start()  # Run function every 15 min
    response = requests.get("http://127.0.0.1:8000/budget/api/latest.json")
    budget = response.json()

    for committee_name in budget:
        try:
            committee = Committee.objects.get(name=committee_name)
        except ObjectDoesNotExist:
            committee = Committee(name=committee_name)
            committee.save()
        for cost_centre_name in budget[committee_name]:
            try:
                cost_centre = CostCentre.objects.get(name=cost_centre_name, committee=committee)
            except ObjectDoesNotExist:
                cost_centre = CostCentre(name=cost_centre_name, committee=committee)
                cost_centre.save()
            for budget_line_name in budget[committee_name][cost_centre_name]:
                try:
                    BudgetLine.objects.get(name=budget_line_name, cost_centre=cost_centre)
                except ObjectDoesNotExist:
                    budget_line = BudgetLine(name=budget_line_name, cost_centre=cost_centre)
                    budget_line.save()
