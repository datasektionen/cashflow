from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import ClaimPartAttestView, ClaimPartUnattestView, PaymentViewSet

router = SimpleRouter()
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = router.urls + [
    path(
        "claim-parts/<int:pk>/attest/",
        ClaimPartAttestView.as_view(),
        name="claim-part-attest",
    ),
    path(
        "claim-parts/<int:pk>/unattest/",
        ClaimPartUnattestView.as_view(),
        name="claim-part-unattest",
    ),
]
