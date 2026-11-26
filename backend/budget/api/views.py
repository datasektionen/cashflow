from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Q
from django.db.models.aggregates import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from budget.api.serializers import (
    BudgetLineSerializer,
    BudgetYearQuerySerializer,
    CostCentreSerializer,
    CostCentreSummarySerializer,
    SecondaryCostCentreSerializer,
)
from cashflow.api.filters import (
    apply_budget_line_filter,
    apply_cost_centre_filter,
    apply_secondary_cost_centre_filter,
)
from cashflow.gordian import (
    list_budget_lines_from_gordian,
    list_cost_centres_from_gordian,
    list_secondary_cost_centres_from_gordian,
)
from core.api.utils import AuthenticatedUserMixin
from core.models import ClaimPart


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

    def get(self, request):

        name = request.query_params.get("name")

        gordian_ccs = list_cost_centres_from_gordian()
        blown_ccs = _blown_cost_centres()

        if name is not None:
            result = [
                {
                    **cc.model_dump(),
                    "active": True,
                    "contains_blown": _normalise(cc.name) in blown_ccs,
                }
                for cc in gordian_ccs
                if cc.name == name
            ]
        else:
            active_names = {cc.name for cc in gordian_ccs}
            active = [
                {
                    **cc.model_dump(),
                    "active": True,
                    "contains_blown": _normalise(cc.name) in blown_ccs,
                }
                for cc in gordian_ccs
            ]

            ccs = ClaimPart.objects.values_list("cost_centre", flat=True).distinct()
            inactive_names = {
                cc_name for cc_name in ccs if cc_name and cc_name not in active_names
            }
            inactive = [
                {
                    "id": None,
                    "name": cc_name,
                    "type": None,
                    "active": False,
                }
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

            sccs = ClaimPart.objects.values_list(
                "secondary_cost_centre", flat=True
            ).distinct()
            inactive_names = {
                scc_name
                for scc_name in sccs
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

    def get(self, request):

        gordian_bls = list_budget_lines_from_gordian()
        active_names = {bl.name for bl in gordian_bls}
        active = [{**bl.model_dump(), "active": True} for bl in gordian_bls]

        bls = ClaimPart.objects.values_list("budget_line", flat=True).distinct()
        inactive_names = {
            bl_name for bl_name in bls if bl_name and bl_name not in active_names
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


def _normalise(name: str) -> str:
    return " ".join(name.split()).lower()


def _line_key(cc: str, scc: str, bl: str) -> tuple[str, str, str]:
    """The key `_amounts_by_line` uses for a cost centre/secondary/budget line name."""
    return (_normalise(cc), _normalise(scc), _normalise(bl))


def _query_year(request: Request) -> int:
    query = BudgetYearQuerySerializer(data=request.query_params)
    query.is_valid(raise_exception=True)
    return query.validated_data.get("year") or timezone.localdate().year


def _is_blown(budget: int, uploaded: Decimal) -> bool:
    """Whether a budget line has been overspent.

    GOrdian stores expense budgets as negative numbers, and uses 0 for lines
    without an expense budget (which can't be blown).
    """
    return bool(budget) and uploaded > abs(budget)


def _amounts_by_line(year: int) -> dict[tuple[str, str, str], dict[str, Decimal]]:
    """Returns a (cc, scc, bl) -> Decimal map with the total amounts uploaded/attested/paid for each budget line"""
    year_start = date(year, 1, 1)
    year_end = date(year + 1, 1, 1)

    rows = (
        ClaimPart.objects.alias(
            effective_date=Coalesce(
                "claim__expense_data__expense_date",
                "claim__invoice_data__invoice_date",
                "claim__invoice_data__paid_at",
            )
        )
        .filter(effective_date__gte=year_start, effective_date__lt=year_end)
        .values("cost_centre", "secondary_cost_centre", "budget_line")
        .annotate(
            uploaded=Sum("amount"),
            attested=Sum("amount", filter=Q(attested_by__isnull=False)),
            paid=Sum(
                "amount",
                filter=Q(claim__expense_data__reimbursement__isnull=False)
                | Q(claim__invoice_data__paid_at__isnull=False),
            ),
        )
    )

    totals: dict[tuple[str, str, str], dict[str, Decimal]] = defaultdict(
        lambda: {field: Decimal(0) for field in _AMOUNT_FIELDS}
    )
    for row in rows:
        entry = totals[
            _line_key(
                row["cost_centre"], row["secondary_cost_centre"], row["budget_line"]
            )
        ]
        entry["uploaded"] += row["uploaded"] or Decimal(0)
        entry["attested"] += row["attested"] or Decimal(0)
        entry["paid"] += row["paid"] or Decimal(0)

    return totals


def _blown_cost_centres(year: int | None = None) -> set[str]:
    year = year or timezone.localdate().year
    bl_totals = _amounts_by_line(year)

    scc_by_id = {scc.id: scc for scc in list_secondary_cost_centres_from_gordian()}
    cc_name_by_id = {cc.id: cc.name for cc in list_cost_centres_from_gordian()}

    # We need to convert from GOrdian budget lines (using IDs), to Cashflow's
    # <cc name>/<scc name>/<bl name>
    budget_by_line: dict[tuple[str, str, str], int] = {}
    for bl in list_budget_lines_from_gordian():
        scc = scc_by_id.get(bl.scc_id)
        if scc is None:
            continue
        cc_name = cc_name_by_id.get(scc.cc_id)
        if cc_name is None:
            continue
        budget_by_line[_line_key(cc_name, scc.name, bl.name)] = bl.expense

    blown: set[str] = set()
    for key, amounts in bl_totals.items():
        budget = budget_by_line.get(key)
        if budget is not None and _is_blown(budget, amounts["uploaded"]):
            blown.add(key[0])
    return blown


@dataclass
class _CostCentreTotals:
    id: int
    name: str
    type: str
    income: int = 0
    expense: int = 0
    blown_lines: int = 0
    amount_uploaded: Decimal = Decimal(0)
    amount_attested: Decimal = Decimal(0)
    amount_paid: Decimal = Decimal(0)


class CostCentreSummaryList(APIView, AuthenticatedUserMixin):
    """Budget and claimed totals per GOrdian cost centre for one year.

    `expense` and `income` are the summed GOrdian budgets (expense as a positive
    number). The amounts are summed over every claim part on the cost centre
    that year, including parts on budget lines no longer on GOrdian.
    """

    def get(self, request: Request) -> Response:
        amounts = _amounts_by_line(_query_year(request))
        cost_centres = list_cost_centres_from_gordian()
        cc_by_id = {cc.id: cc for cc in cost_centres}
        scc_by_id = {scc.id: scc for scc in list_secondary_cost_centres_from_gordian()}

        totals = {
            cc.id: _CostCentreTotals(id=cc.id, name=cc.name, type=cc.type)
            for cc in cost_centres
        }

        zero = {field: Decimal(0) for field in _AMOUNT_FIELDS}
        for bl in list_budget_lines_from_gordian():
            scc = scc_by_id.get(bl.scc_id)
            if scc is None or scc.cc_id not in cc_by_id:
                continue
            cc = cc_by_id[scc.cc_id]
            entry = totals[cc.id]
            entry.income += bl.income
            entry.expense += abs(bl.expense)
            line = amounts.get(_line_key(cc.name, scc.name, bl.name), zero)
            if _is_blown(bl.expense, line["uploaded"]):
                entry.blown_lines += 1

        cc_id_by_name = {_normalise(cc.name): cc.id for cc in cost_centres}
        for (cc_name, _, _), line in amounts.items():
            cc_id = cc_id_by_name.get(cc_name)
            if cc_id is None:
                continue
            entry = totals[cc_id]
            entry.amount_uploaded += line["uploaded"]
            entry.amount_attested += line["attested"]
            entry.amount_paid += line["paid"]

        return Response(CostCentreSummarySerializer(totals.values(), many=True).data)


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

        amounts = _amounts_by_line(_query_year(request))
        zero = {field: Decimal(0) for field in _AMOUNT_FIELDS}

        scc_data = []
        for scc in secondary_cost_centres:
            budget_lines = []
            for bl in list_budget_lines_from_gordian(secondary_cost_center=scc.id):
                line_amounts = amounts.get(
                    _line_key(cost_centre.name, scc.name, bl.name), zero
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
                        "blown": _is_blown(bl.expense, line_amounts["uploaded"]),
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


class BudgetLineDetailView(APIView, AuthenticatedUserMixin):
    def get(self, request: Request, budget_line_id: int) -> Response:
        try:
            budget_line = next(
                bl for bl in list_budget_lines_from_gordian() if bl.id == budget_line_id
            )
        except StopIteration:
            raise NotFound(f"No budget_line with id {budget_line_id} found")

        scc = next(
            scc
            for scc in list_secondary_cost_centres_from_gordian()
            if scc.id == budget_line.scc_id
        )
        cc = next(cc for cc in list_cost_centres_from_gordian() if cc.id == scc.cc_id)

        amounts = _amounts_by_line(_query_year(request))
        line_amounts = amounts.get(
            _line_key(cc.name, scc.name, budget_line.name),
            {field: Decimal(0) for field in _AMOUNT_FIELDS},
        )

        data = {
            "id": budget_line.id,
            "name": budget_line.name,
            "secondary_cost_centre_id": scc.id,
            "accounts": budget_line.account,
            "income": budget_line.income,
            "expense": budget_line.expense,
            "comment": budget_line.comment,
            "active": True,
            "amount_uploaded": line_amounts["uploaded"],
            "amount_attested": line_amounts["attested"],
            "amount_paid": line_amounts["paid"],
            "blown": _is_blown(budget_line.expense, line_amounts["uploaded"]),
        }

        return Response(BudgetLineSerializer(data).data)
