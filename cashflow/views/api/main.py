from rest_framework.response import Response
from rest_framework.views import APIView

from cashflow.gordian import list_cost_centres_from_gordian, list_secondary_cost_centres_from_gordian, \
    list_budget_lines_from_gordian


class CostCenterList(APIView):
    """View to list all cost centers currently on GOrdian."""

    def get(self, request):

        name = request.query_params.get("name")
        if name is not None:
            cost_centers = [cc.model_dump() for cc in list_cost_centres_from_gordian() if cc.name == name]
        else:
            cost_centers = [cc.model_dump() for cc in list_cost_centres_from_gordian()]

        return Response(cost_centers, content_type="application/json")


class SecondaryCostCenterList(APIView):

    def get(self, request):

        costcenter_id = request.query_params.get("costcenter_id")
        if costcenter_id is not None:
            collection = [scc.model_dump() for scc in list_secondary_cost_centres_from_gordian() if
                          scc.cc_id == int(costcenter_id)]
        else:
            collection = list_secondary_cost_centres_from_gordian()

        return Response(collection, content_type="application/json")


class BudgetLineList(APIView):

    def get(self, request):

        scc_id = request.query_params.get("secondarycostcenter_id")
        if scc_id is not None:
            collection = [bl.model_dump() for bl in list_budget_lines_from_gordian(int(scc_id))]
        else:
            collection = list_budget_lines_from_gordian()

        return Response(collection, content_type="application/json")
