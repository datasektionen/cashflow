from django.urls import path

from fortnox.api.views import (
    FortnoxAccountList,
    FortnoxCostCentreList,
    FortnoxDisconnectView,
    FortnoxStatusView,
)

urlpatterns = [
    path("status/", FortnoxStatusView.as_view(), name="fortnox-status"),
    path("disconnect/", FortnoxDisconnectView.as_view(), name="fortnox-disconnect"),
    path("accounts/", FortnoxAccountList.as_view(), name="fortnox-accounts"),
    path(
        "cost-centres/",
        FortnoxCostCentreList.as_view(),
        name="fortnox-cost-centres",
    ),
]
