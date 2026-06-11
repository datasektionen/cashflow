from django.conf import settings
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import inline_serializer
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from cashflow.gordian import (
    list_cost_centres_from_gordian,
    list_secondary_cost_centres_from_gordian,
    list_budget_lines_from_gordian,
)
from .serializers import (
    CostCentreSerializer,
    SecondaryCostCentreSerializer,
    BudgetLineSerializer,
)


class CostCentreList(GenericAPIView):
    """List cost centres from GOrdian.

    Returns every cost centre currently registered on GOrdian. Pass the
    `name` query parameter to filter the result to cost centres with that
    exact name.
    """

    def get_serializer_class(self):
        return CostCentreSerializer

    # extend_schema allows us to annotate endpoints in Redoc better
    @extend_schema(
        summary="List cost centres",
        operation_id="list_cost_centres",
        tags=["Budget"],
    )
    def get(self, request):

        name = request.query_params.get("name")
        if name is not None:
            cost_centres = [
                cc.model_dump()
                for cc in list_cost_centres_from_gordian()
                if cc.name == name
            ]
        else:
            cost_centres = [cc.model_dump() for cc in list_cost_centres_from_gordian()]

        return Response(CostCentreSerializer(cost_centres, many=True).data)


class SecondaryCostCentreList(GenericAPIView):
    """List secondary cost centres from GOrdian.

    Returns every secondary cost centre on GOrdian. Pass the
    `costcentre_id` query parameter to restrict the result to children of a
    specific cost centre.
    """

    def get_serializer_class(self):
        return SecondaryCostCentreSerializer

    @extend_schema(
        summary="List secondary cost centres",
        operation_id="list_secondary_cost_centres",
        tags=["Budget"],
    )
    def get(self, request):

        costcentre_id = request.query_params.get("costcentre_id")
        if costcentre_id is not None:
            collection = [
                scc.model_dump()
                for scc in list_secondary_cost_centres_from_gordian()
                if scc.cc_id == int(costcentre_id)
            ]
        else:
            collection = list_secondary_cost_centres_from_gordian()

        collection = SecondaryCostCentreSerializer(collection, many=True)
        return Response(collection.data)


class BudgetLineList(GenericAPIView):
    """List budget lines from GOrdian.

    Returns every budget line on GOrdian. Pass the `secondarycostcentre_id`
    query parameter to restrict the result to budget lines belonging to a
    specific secondary cost centre.
    """

    def get_serializer_class(self):
        return BudgetLineSerializer

    @extend_schema(
        summary="List budget lines",
        operation_id="list_budget_lines",
        tags=["Budget"],
    )
    def get(self, request):

        scc_id = request.query_params.get("secondarycostcentre_id")
        if scc_id is not None:
            collection = [
                bl.model_dump() for bl in list_budget_lines_from_gordian(int(scc_id))
            ]
        else:
            collection = list_budget_lines_from_gordian()

        collection = BudgetLineSerializer(collection, many=True)
        return Response(collection.data)


class FeaturesList(APIView):
    @extend_schema(
        summary="List enabled features",
        description="Returns true/false for which optional features are enabled on this instance.",
        operation_id="list_features",
        tags=["Features"],
        responses=inline_serializer(
            name="Features",
            fields={"fortnox": serializers.BooleanField()},
        ),
    )
    def get(self, request):
        return Response({"fortnox": settings.FORTNOX_ENABLED})
