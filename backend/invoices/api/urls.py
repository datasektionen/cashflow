from django.urls import path
from rest_framework.routers import SimpleRouter

from invoices.api.views import (
    InvoiceViewSet,
    InvoicePartAttestView,
    InvoicePartUnattestView,
)

router = SimpleRouter()
router.register(r"invoices", InvoiceViewSet, basename="invoice")
urlpatterns = router.urls + [
    path(
        "invoice-parts/<int:pk>/attest/",
        InvoicePartAttestView.as_view(),
        name="invoice-part-attest",
    ),
    path(
        "invoice-parts/<int:pk>/unattest/",
        InvoicePartUnattestView.as_view(),
        name="invoice-part-unattest",
    ),
]
