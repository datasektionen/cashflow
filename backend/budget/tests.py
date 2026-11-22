from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from cashflow.gordian import GBudgetLine, GCostCenter, GSecondaryCostCenter
from core.factories import ProfileFactory
from core.models import Claim, ClaimPart
from expenses.models import ExpenseData

URL = "/api/cost-centres/summary/"


def cost_centre(id, name, type="committee"):
    return GCostCenter(CostCentreID=id, CostCentreName=name, CostCentreType=type)


def secondary(id, cc_id, name):
    return GSecondaryCostCenter(
        SecondaryCostCentreID=id, CostCentreID=cc_id, SecondaryCostCentreName=name
    )


def line(id, scc_id, name, expense, income=0):
    return GBudgetLine(
        BudgetLineID=id,
        SecondaryCostCentreID=scc_id,
        BudgetLineName=name,
        BudgetLineAccount="",
        BudgetLineIncome=income,
        BudgetLineExpense=expense,
        BudgetLineComment="",
    )


def claim_part(profile, cc, scc, bl, amount, on=date(2026, 3, 1)):
    data = ExpenseData.objects.create(expense_date=on)
    claim = Claim.objects.create(owner=profile, description="x", expense_data=data)
    return ClaimPart.objects.create(
        claim=claim,
        cost_centre=cc,
        secondary_cost_centre=scc,
        budget_line=bl,
        amount=Decimal(amount),
    )


@pytest.fixture
def gordian(mocker):
    mocker.patch(
        "budget.api.views.list_cost_centres_from_gordian",
        return_value=[cost_centre(1, "Ada"), cost_centre(2, "Dive", "project")],
    )
    mocker.patch(
        "budget.api.views.list_secondary_cost_centres_from_gordian",
        return_value=[secondary(10, 1, "Allmänt"), secondary(20, 2, "Fest")],
    )
    mocker.patch(
        "budget.api.views.list_budget_lines_from_gordian",
        return_value=[
            line(100, 10, "Mat", -1000, income=200),
            line(101, 10, "Pynt", -500),
            line(200, 20, "Hyra", -3000, income=4000),
        ],
    )


def by_name(response):
    return {row["name"]: row for row in response.data}


def test_sums_budgets_and_claimed_amounts_per_cost_centre(api_client, user, gordian):
    profile = ProfileFactory(user=user)
    claim_part(profile, "Ada", "Allmänt", "Mat", "1200")
    claim_part(profile, "ada", "Allmänt", "Pynt", "100")
    claim_part(profile, "Ada", "Allmänt", "Mat", "50", on=date(2025, 12, 31))

    response = api_client.get(URL, {"year": 2026})

    assert response.status_code == 200
    ada = by_name(response)["Ada"]
    assert ada["expense"] == 1500
    assert ada["income"] == 200
    assert Decimal(ada["amount_uploaded"]) == Decimal("1300")
    assert ada["blown_lines"] == 1
    dive = by_name(response)["Dive"]
    assert dive["type"] == "project"
    assert Decimal(dive["amount_uploaded"]) == 0
    assert dive["blown_lines"] == 0


def test_counts_claims_on_lines_missing_from_gordian(api_client, user, gordian):
    claim_part(ProfileFactory(user=user), "Dive", "Gammalt", "Borttagen", "75")

    response = api_client.get(URL, {"year": 2026})

    assert Decimal(by_name(response)["Dive"]["amount_uploaded"]) == Decimal("75")


def test_rejects_invalid_year(api_client, gordian):
    assert api_client.get(URL, {"year": "abc"}).status_code == 400


def test_detail_rejects_invalid_year(api_client, gordian):
    response = api_client.get("/api/cost-centres/1/", {"year": "2.5"})
    assert response.status_code == 400


def test_requires_authentication(db, gordian):
    assert APIClient().get(URL).status_code == 403
