from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from expenses.api_views.accounting import AccountingViewSet
from expenses.api_views.attest import AttestViewSet
from expenses.api_views.comment import CommentViewSet
from expenses.api_views.expense import ExpenseViewSet
from expenses.api_views.file import FileViewSet
from expenses.api_views.misc import budget, login, logout, set_firebase_instance_id, committees, cost_centres
from expenses.api_views.pay import PaymentViewSet
from expenses.api_views.user import UserViewSet

router = DefaultRouter()
router.register('api/expense', ExpenseViewSet, base_name='Expense')
router.register('api/payment', PaymentViewSet, base_name='Payment')
router.register('api/comment', CommentViewSet, base_name='Comment')
router.register('api/user', UserViewSet, base_name='User')
router.register('api/attest', AttestViewSet, base_name='Attest')
router.register('api/accounting', AccountingViewSet, base_name='Accounting')
router.register('api/file', FileViewSet, base_name='File')
urlpatterns = router.urls

urlpatterns.append(url(r'^api/budget/$', budget))
urlpatterns.append(url(r'^api/firebase_instance_id/$', set_firebase_instance_id))
urlpatterns.append(url(r'^api/committees/$', committees))
urlpatterns.append(url(r'^api/cost_centre/(\d+)/$', cost_centres))

urlpatterns.append(url(r'^login/(.*)/$', login))
urlpatterns.append(url(r'^logout/$', logout))
