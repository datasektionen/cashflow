from django.urls import path
from rest_framework.routers import SimpleRouter

from core.api.views import ClaimPartAttestView, ClaimPartUnattestView
from invoices.api.views import InvoiceViewSet

router = SimpleRouter()
router.register(r"invoices", InvoiceViewSet, basename="invoice")
urlpatterns = router.urls + [
    # Legacy aliases for claim-parts/<pk>/(un)attest/
    path(
        "invoice-parts/<int:pk>/attest/",
        ClaimPartAttestView.as_view(),
        name="invoice-part-attest",
    ),
    path(
        "invoice-parts/<int:pk>/unattest/",
        ClaimPartUnattestView.as_view(),
        name="invoice-part-unattest",
    ),
]
