from django.conf import settings
from django.urls import include, path

from . import views
from core.api.views import (
    ActionOverview,
    ActionSummary,
    ClaimsList,
    VoucherSeriesList,
)

urlpatterns = [
    path("features/", views.FeaturesList.as_view(), name="feature-flags"),
    path("claims/", ClaimsList.as_view(), name="claims-list"),
    path("actions/", ActionSummary.as_view(), name="action-summary"),
    path("actions/overview/", ActionOverview.as_view(), name="action-overview"),
    path(
        "voucher-series/",
        VoucherSeriesList.as_view(),
        name="voucherseries-list",
    ),
    path("", include("budget.api.urls")),
    path("", include("expenses.api.urls")),
    path("", include("invoices.api.urls")),
    path("users/", include("users.api.urls")),
    path("", include("core.api.urls")),
    path("stats/", include("stats.api.urls")),
]

if settings.FORTNOX_ENABLED:
    urlpatterns += [path("fortnox/", include("fortnox.api.urls"))]
