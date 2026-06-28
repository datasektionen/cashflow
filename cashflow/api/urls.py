from django.conf import settings
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView

from . import views
from core.api.views import ActionSummary, ClaimsList

urlpatterns = [
    path("features/", views.FeaturesList.as_view(), name="feature-flags"),
    path("claims/", ClaimsList.as_view(), name="claims-list"),
    path("actions/", ActionSummary.as_view(), name="action-summary"),
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
    path("", include("core.api.urls")),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularRedocView.as_view(url_name="schema"), name="docs"),
]

if settings.FORTNOX_ENABLED:
    urlpatterns += [path("fortnox/", include("fortnox.api.urls"))]
