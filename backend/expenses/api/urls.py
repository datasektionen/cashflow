from django.urls import path
from rest_framework.routers import SimpleRouter

from core.api.views import ClaimPartAttestView, ClaimPartUnattestView
from expenses.api.views import ExpenseViewSet

# The router automatically generates URL patterns for a ViewSet (list, detail, and any @action methods).
router = SimpleRouter()
router.register(r"expenses", ExpenseViewSet, basename="expense")
urlpatterns = router.urls + [
    # Legacy aliases for claim-parts/<pk>/(un)attest/
    path(
        "expense-parts/<int:pk>/attest/",
        ClaimPartAttestView.as_view(),
        name="expense-part-attest",
    ),
    path(
        "expense-parts/<int:pk>/unattest/",
        ClaimPartUnattestView.as_view(),
        name="expense-part-unattest",
    ),
]
