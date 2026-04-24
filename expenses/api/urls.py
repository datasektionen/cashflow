from rest_framework.routers import SimpleRouter

from expenses.api.views import ExpenseViewSet

# The router automatically generates URL patterns for a ViewSet (list, detail, and any @action methods).
router = SimpleRouter()
router.register(r'expenses', ExpenseViewSet, basename='expense')
urlpatterns = router.urls
