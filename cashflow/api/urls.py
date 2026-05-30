from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView

from . import views

urlpatterns = [
    path(
        "cost-centres/",
        views.CostCentreList.as_view(),
        name="costcentre-list",
    ),
    path(
        "secondary-cost-centres/",
        views.SecondaryCostCentreList.as_view(),
        name="secondarycostcentre-list",
    ),
    path(
        "budget-lines/",
        views.BudgetLineList.as_view(),
        name="budgetline-list",
    ),
    path("", include("expenses.api.urls")),
    path("", include("invoices.api.urls")),
    path("users/", include("users.api.urls")),
    path("files/", include("file_api.urls")),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularRedocView.as_view(url_name="schema"), name="docs"),
]
