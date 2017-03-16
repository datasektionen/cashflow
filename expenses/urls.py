from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from expenses.views.accounting import AccountingViewSet
from expenses.views.attest import AttestViewSet
from expenses.views.comment import CommentViewSet
from expenses.views.expense import ExpenseViewSet
from expenses.views.file import FileViewSet
from expenses.views.misc import budget, login, logout
from expenses.views.pay import PaymentViewSet
from expenses.views.user import UserViewSet

router = DefaultRouter()
router.register('expense', ExpenseViewSet, base_name='Expense')
router.register('payment', PaymentViewSet, base_name='Payment')
router.register('comment', CommentViewSet, base_name='Comment')
router.register('user', UserViewSet, base_name='User')
router.register('attest', AttestViewSet, base_name='Attest')
router.register('accounting', AccountingViewSet, base_name='Accounting')
router.register('file', FileViewSet, base_name='File')
urlpatterns = router.urls

urlpatterns.append(url(r'^budget/$', budget))
urlpatterns.append(url(r'^login/(.*)/$', login))
urlpatterns.append(url(r'^logout/$', logout))
