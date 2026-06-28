from django.urls import path

from fortnox.api.views import FortnoxDisconnectView, FortnoxStatusView

urlpatterns = [
    path("status/", FortnoxStatusView.as_view(), name="fortnox-status"),
    path("disconnect/", FortnoxDisconnectView.as_view(), name="fortnox-disconnect"),
]
