from django.urls import path
from rest_framework.routers import SimpleRouter

from expenses.api.views import ExpenseViewSet, ExpensePartAttestView

# The router automatically generates URL patterns for a ViewSet (list, detail, and any @action methods).
router = SimpleRouter()
router.register(r"expenses", ExpenseViewSet, basename="expense")
urlpatterns = router.urls + [
    path(
        "expense-parts/<int:pk>/attest/",
        ExpensePartAttestView.as_view(),
        name="expense-part-attest",
    ),
]
