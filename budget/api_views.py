import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, JsonResponse, HttpResponseForbidden

from budget import models
from cashflow import dauth


# Valid input:
# {
#   <committee>: {
#       <cost_centre>: {
#           <budget_line>: {
#               <optional>"amount": <int>,
#               <optional>"spent": <int>,
#               <optional>"booking": [<int>]
#           }
#       }
#   }
# }
def add_budget(request, year):
    if not dauth.has_permission('admin', request):
        return HttpResponseForbidden()
    if request.method == 'POST':
        try:
            year = models.Year.objects.get(name=year)
        except ObjectDoesNotExist:
            raise Http404("Året finns inte")

        budget = json.loads(request.body.decode('utf-8'))
        for committee in budget:
            try:
                committee_object = models.Committee.objects.get(year=year, name=committee)
            except ObjectDoesNotExist:
                committee_object = models.Committee(year=year, name=committee)
                committee_object.save()
            for cost_centre in budget[committee]:
                try:
                    costcentre_object = models.CostCentre.objects.get(committee=committee_object, name=cost_centre)
                except ObjectDoesNotExist:
                    costcentre_object = models.CostCentre(committee=committee_object, name=cost_centre)
                    costcentre_object.save()
                for budget_line in budget[committee][cost_centre]:
                    try:
                        budgetline_object = models.BudgetLine.objects.get(cost_centre=costcentre_object,
                                                                          name=budget_line)
                    except ObjectDoesNotExist:
                        budgetline_object = models.BudgetLine(cost_centre=costcentre_object, name=budget_line)

                    if 'amount' in budget[committee][cost_centre][budget_line]:
                        budgetline_object.amount = budget[committee][cost_centre][budget_line]['amount']
                    if 'spent' in budget[committee][cost_centre][budget_line]:
                        budgetline_object.spent = budget[committee][cost_centre][budget_line]['spent']
                    budgetline_object.save()
                    for booking_account in budget[committee][cost_centre][budget_line]['booking']:
                        try:
                            bookingaccount_object = models.BookingAccount.objects.get(number=int(booking_account))
                        except ObjectDoesNotExist:
                            bookingaccount_object = models.BookingAccount(number=int(booking_account), name="")
                            bookingaccount_object.save()
                        bookingaccount_object.budgetlines.add(budgetline_object)

        return JsonResponse({"response": "Success"})
    else:
        raise Http404()


def latest_as_json(request):
    if request.method == 'GET':
        budget = {}
        for committee in models.Committee.objects.filter(year=models.Year.objects.latest('id')).order_by('name'):
            budget[str(committee.name)] = {}
            for cost_centre in models.CostCentre.objects.filter(committee=committee).order_by('name'):
                budget[str(committee.name)][str(cost_centre.name)] = []
                for budget_line in models.BudgetLine.objects.filter(cost_centre=cost_centre).order_by('name'):
                    budget[str(committee.name)][str(cost_centre.name)].append(str(budget_line.name))

        return JsonResponse(budget)
    else:
        raise Http404()
