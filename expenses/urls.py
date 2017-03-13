from rest_framework.routers import DefaultRouter

from expenses.views.expense import ExpenseViewSet

router = DefaultRouter()
router.register('expense', ExpenseViewSet, base_name='Expense')

urlpatterns = router.urls
