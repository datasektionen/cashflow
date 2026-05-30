from rest_framework.routers import SimpleRouter

from invoices.api.views import InvoiceViewSet

router = SimpleRouter()
router.register(r"invoices", InvoiceViewSet, basename="invoice")
urlpatterns = router.urls
