from django.urls import re_path
from rest_framework.routers import DefaultRouter

import expenses.api_views.accounting as accounting_api
import expenses.api_views.attest as attest_api
import expenses.api_views.comment as comment_api
import expenses.api_views.expense as expense_api
import expenses.api_views.file as file_api
import expenses.api_views.misc as misc_api
import expenses.api_views.pay as pay_api
import expenses.api_views.user as user_api
import expenses.views as views

router = DefaultRouter()
router.register('expense',  expense_api.ExpenseViewSet, basename='Expense')
router.register('payment', pay_api.PaymentViewSet, basename='Payment')
router.register('comment', comment_api.CommentViewSet, basename='Comment')
router.register('user', user_api.UserViewSet, basename='User')
router.register('attest', attest_api.AttestViewSet, basename='Attest')
router.register('accounting', accounting_api.AccountingViewSet, basename='Accounting')
router.register('file', file_api.FileViewSet, basename='File')
api_urlpatterns = router.urls

api_urlpatterns.append(re_path(r'^firebase_instance_id/$', misc_api.set_firebase_instance_id))
api_urlpatterns.append(re_path(r'^login/(.*)/$', misc_api.login, name='expenses-api-login'))
api_urlpatterns.append(re_path(r'^logout/$', misc_api.logout))

urlpatterns = [
    re_path(r'^new/$', views.new_expense, name='expenses-new'),
    re_path(r'^new/confirmation/(?P<pk>\d+)/$', views.expense_new_confirmation, name='expenses-new-confirmation'),
    re_path(r'^(?P<pk>\d+)/$', views.get_expense, name='expenses-show'),
    re_path(r'^(?P<pk>\d+)/edit/$', views.edit_expense, name='expenses-edit'),
    re_path(r'^(?P<pk>\d+)/delete/$', views.delete_expense, name='expenses-delete'),
    re_path(r'^(?P<expense_pk>\d+)/comment/$', views.new_comment, name='expenses-comment'),

    re_path(r'^api/payment/new/$', views.api_new_payment, name='expenses-api-payment-new'),
    re_path(r'^payment/new/$', views.new_payment, name='expenses-payment-new'),
    re_path(r'^payment/(?P<pk>\d+)/$', views.get_payment, name='expenses-payment'),
]
