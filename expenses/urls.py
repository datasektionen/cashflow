from rest_framework.routers import DefaultRouter

from expenses.views.comment import CommentViewSet
from expenses.views.expense import ExpenseViewSet
from expenses.views.pay import PaymentViewSet
from expenses.views.user import UserViewSet

router = DefaultRouter()
router.register('expense', ExpenseViewSet, base_name='Expense')
router.register('payment', PaymentViewSet, base_name='Payment')
router.register('comment', CommentViewSet, base_name='Comment')
router.register('user', UserViewSet, base_name='User')
urlpatterns = router.urls
