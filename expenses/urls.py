from rest_framework.routers import DefaultRouter

from expenses.views.expense import ExpenseView

router = DefaultRouter()
router.register('expense', ExpenseView, base_name='Expense')

urlpatterns = router.urls
