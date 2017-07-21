from django.http import Http404, JsonResponse

from budget import models


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
