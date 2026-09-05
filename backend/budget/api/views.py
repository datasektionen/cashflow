from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.db.models import Q
from django.db.models.aggregates import Sum
from django.db.models.functions import Coalesce, Upper
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from cashflow.api.filters import (
    apply_cost_centre_filter,
    apply_secondary_cost_centre_filter,
    apply_budget_line_filter,
)
from budget.api.serializers import (
    CostCentreSerializer,
    SecondaryCostCentreSerializer,
    BudgetLineSerializer,
)
from cashflow.gordian import (
    list_cost_centres_from_gordian,
    list_secondary_cost_centres_from_gordian,
    list_budget_lines_from_gordian,
)
from core.api.utils import AuthenticatedUserMixin
from expenses.models import ExpensePart
from invoices.models import InvoicePart


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


_AMOUNT_FIELDS = ("uploaded", "attested", "paid")


def _amounts_by_line(year: int) -> dict[tuple[str, str, str], dict[str, Decimal]]:
    year_start = date(year, 1, 1)
    year_end = date(year + 1, 1, 1)

    expense_rows = (
        ExpensePart.objects.filter(
            expense__expense_date__gte=year_start,
            expense__expense_date__lt=year_end,
        )
        .values(
            cc=Upper("cost_centre"),
            scc=Upper("secondary_cost_centre"),
            bl=Upper("budget_line"),
        )
        .annotate(
            uploaded=Sum("amount"),
            attested=Sum("amount", filter=Q(attested_by__isnull=False)),
            paid=Sum("amount", filter=Q(expense__reimbursement__isnull=False)),
        )
    )
    invoice_rows = (
        InvoicePart.objects.alias(
            effective_date=Coalesce("invoice__invoice_date", "invoice__payed_at")
        )
        .filter(effective_date__gte=year_start, effective_date__lt=year_end)
        .values(
            cc=Upper("cost_centre"),
            scc=Upper("secondary_cost_centre"),
            bl=Upper("budget_line"),
        )
        .annotate(
            uploaded=Sum("amount"),
            attested=Sum("amount", filter=Q(attested_by__isnull=False)),
            paid=Sum("amount", filter=Q(invoice__payed_at__isnull=False)),
        )
    )

    totals: dict[tuple[str, str, str], dict[str, Decimal]] = defaultdict(
        lambda: {field: Decimal("0") for field in _AMOUNT_FIELDS}
    )
    for row in (*expense_rows, *invoice_rows):
        entry = totals[(row["cc"], row["scc"], row["bl"])]
        entry["uploaded"] += row["uploaded"] or Decimal("0")
        entry["attested"] += row["attested"] or Decimal("0")
        entry["paid"] += row["paid"] or Decimal("0")
    return totals


class CostCentreDetailView(APIView, AuthenticatedUserMixin):

    def get(self, request: Request, cost_centre_id: int) -> Response:
        try:
            cost_centre = next(
                cc for cc in list_cost_centres_from_gordian() if cc.id == cost_centre_id
            )
        except StopIteration:
            raise NotFound(f"No cost_centre with id {cost_centre_id} found")

        secondary_cost_centres = list_secondary_cost_centres_from_gordian(
            cost_center=cost_centre.id
        )

        year = int(request.query_params.get("year") or date.today().year)

        amounts = _amounts_by_line(year)
        zero = {field: Decimal("0") for field in _AMOUNT_FIELDS}

        scc_data = []
        for scc in secondary_cost_centres:
            budget_lines = []
            for bl in list_budget_lines_from_gordian(secondary_cost_center=scc.id):
                line_amounts = amounts.get(
                    (cost_centre.name.upper(), scc.name.upper(), bl.name.upper()),
                    zero,
                )
                budget_lines.append(
                    {
                        "id": bl.id,
                        "name": bl.name,
                        "secondary_cost_centre_id": scc.id,
                        "accounts": bl.account,
                        "income": bl.income,
                        "expense": bl.expense,
                        "comment": bl.comment,
                        "active": True,
                        "amount_uploaded": line_amounts["uploaded"],
                        "amount_attested": line_amounts["attested"],
                        "amount_paid": line_amounts["paid"],
                    }
                )

            scc_data.append(
                {
                    "id": scc.id,
                    "name": scc.name,
                    "cost_centre_id": scc.cc_id,
                    "active": True,
                    "budget_lines": budget_lines,
                }
            )

        data = {
            "id": cost_centre.id,
            "name": cost_centre.name,
            "type": cost_centre.type,
            "active": True,
            "secondary_cost_centres": scc_data,
        }

        return Response(CostCentreSerializer(data).data)
