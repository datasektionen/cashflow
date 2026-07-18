from django.urls import path
from rest_framework.routers import SimpleRouter

from invoices.api.views import InvoiceViewSet, InvoicePartAttestView

router = SimpleRouter()
router.register(r"invoices", InvoiceViewSet, basename="invoice")
urlpatterns = router.urls + [
    path(
        "invoice-parts/<int:pk>/attest/",
        InvoicePartAttestView.as_view(),
        name="invoice-part-attest",
    ),
]
