from rest_framework.routers import DefaultRouter

from expenses.views.expense import ExpenseViewSet
from expenses.views.pay import PaymentViewSet

router = DefaultRouter()
router.register('expense', ExpenseViewSet, base_name='Expense')
router.register('payment', PaymentViewSet, base_name='Payment')

urlpatterns = router.urls
