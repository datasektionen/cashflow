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
from expenses.models import ExpensePart
from invoices.models import InvoicePart
from .filters import (
    apply_cost_centre_filter,
    apply_secondary_cost_centre_filter,
    apply_budget_line_filter,
)
from .serializers import (
    CostCentreSerializer,
    SecondaryCostCentreSerializer,
    BudgetLineSerializer,
)


class CostCentreList(GenericAPIView):
    """List cost centres from GOrdian.

    Returns every cost centre currently registered on GOrdian (`active: true`),
    followed by any cost centre referenced on an existing expense or invoice
    that is no longer on GOrdian (`active: false`, `id`/`type` null), sorted
    alphabetically. Pass the `name` query parameter to filter the result to
    cost centres with that exact name.
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
            result = [
                {**cc.model_dump(), "active": True}
                for cc in list_cost_centres_from_gordian()
                if cc.name == name
            ]
        else:
            gordian_ccs = list_cost_centres_from_gordian()
            active_names = {cc.name for cc in gordian_ccs}
            active = [{**cc.model_dump(), "active": True} for cc in gordian_ccs]

            expense_ccs = ExpensePart.objects.values_list(
                "cost_centre", flat=True
            ).distinct()
            invoice_ccs = InvoicePart.objects.values_list(
                "cost_centre", flat=True
            ).distinct()
            inactive_names = {
                cc_name
                for cc_name in (*expense_ccs, *invoice_ccs)
                if cc_name and cc_name not in active_names
            }
            inactive = [
                {"id": None, "name": cc_name, "type": None, "active": False}
                for cc_name in sorted(inactive_names)
            ]

            result = active + inactive
            result = apply_cost_centre_filter(result, request.query_params)

        page = self.paginate_queryset(result)
        if page is not None:
            serializer = CostCentreSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(CostCentreSerializer(result, many=True).data)


class SecondaryCostCentreList(GenericAPIView):
    """List secondary cost centres from GOrdian.

    Returns every secondary cost centre currently registered on GOrdian
    (`active: true`), followed by any secondary cost centre referenced on an
    existing expense or invoice that is no longer on GOrdian (`active: false`,
    `id`/`cost_centre_id` null), sorted alphabetically. Pass the
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
            result = [
                {**scc.model_dump(), "active": True}
                for scc in list_secondary_cost_centres_from_gordian()
                if scc.cc_id == int(costcentre_id)
            ]
        else:
            gordian_sccs = list_secondary_cost_centres_from_gordian()
            active_names = {scc.name for scc in gordian_sccs}
            active = [{**scc.model_dump(), "active": True} for scc in gordian_sccs]

            expense_sccs = ExpensePart.objects.values_list(
                "secondary_cost_centre", flat=True
            ).distinct()
            invoice_sccs = InvoicePart.objects.values_list(
                "secondary_cost_centre", flat=True
            ).distinct()
            inactive_names = {
                scc_name
                for scc_name in (*expense_sccs, *invoice_sccs)
                if scc_name and scc_name not in active_names
            }
            inactive = [
                {"id": None, "name": scc_name, "cc_id": None, "active": False}
                for scc_name in sorted(inactive_names)
            ]

            result = active + inactive
            result = apply_secondary_cost_centre_filter(result, request.query_params)

        page = self.paginate_queryset(result)
        if page is not None:
            serializer = SecondaryCostCentreSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(SecondaryCostCentreSerializer(result, many=True).data)


class BudgetLineList(GenericAPIView):
    """List budget lines from GOrdian.

    Returns every budget line currently registered on GOrdian (`active: true`),
    followed by any budget line referenced on an existing expense or invoice
    that is no longer on GOrdian (`active: false`, other fields null), sorted
    alphabetically. Pass the `secondary_cost_centre` query parameter to
    restrict the result to budget lines belonging to a specific secondary
    cost centre.
    """

    def get_serializer_class(self):
        return BudgetLineSerializer

    @extend_schema(
        summary="List budget lines",
        operation_id="list_budget_lines",
        tags=["Budget"],
    )
    def get(self, request):

        gordian_bls = list_budget_lines_from_gordian()
        active_names = {bl.name for bl in gordian_bls}
        active = [{**bl.model_dump(), "active": True} for bl in gordian_bls]

        expense_bls = ExpensePart.objects.values_list(
            "budget_line", flat=True
        ).distinct()
        invoice_bls = InvoicePart.objects.values_list(
            "budget_line", flat=True
        ).distinct()
        inactive_names = {
            bl_name
            for bl_name in (*expense_bls, *invoice_bls)
            if bl_name and bl_name not in active_names
        }
        inactive = [
            {
                "id": None,
                "name": bl_name,
                "scc_id": None,
                "account": None,
                "income": None,
                "expense": None,
                "comment": None,
                "active": False,
            }
            for bl_name in sorted(inactive_names)
        ]

        result = active + inactive
        result = apply_budget_line_filter(result, request.query_params)

        page = self.paginate_queryset(result)
        if page is not None:
            serializer = BudgetLineSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(BudgetLineSerializer(result, many=True).data)


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
