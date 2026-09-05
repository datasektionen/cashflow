from django.urls import path

from budget.api.views import (
    BudgetLineList,
    CostCentreDetailView,
    CostCentreList,
    SecondaryCostCentreList,
)

urlpatterns = [
    path("cost-centres/", CostCentreList.as_view(), name="costcentre-list"),
    path(
        "cost-centres/<int:cost_centre_id>/",
        CostCentreDetailView.as_view(),
        name="costcentre-detail",
    ),
    path(
        "secondary-cost-centres/",
        SecondaryCostCentreList.as_view(),
        name="secondarycostcentre-list",
    ),
    path("budget-lines/", BudgetLineList.as_view(), name="budgetline-list"),
]
