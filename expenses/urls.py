from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from expenses.views.comment import CommentViewSet
from expenses.views.expense import ExpenseViewSet
from expenses.views.misc import budget, login, logout
from expenses.views.user import UserViewSet
from expenses.views.pay import PaymentViewSet

router = DefaultRouter()
router.register('expense', ExpenseViewSet, base_name='Expense')
router.register('payment', PaymentViewSet, base_name='Payment')
router.register('comment', CommentViewSet, base_name='Comment')
router.register('user', UserViewSet, base_name='User')
urlpatterns = router.urls

urlpatterns.append(url(r'^budget/$', budget))
urlpatterns.append(url(r'^login/(.*)/$', login))
urlpatterns.append(url(r'^logout/$', logout))
