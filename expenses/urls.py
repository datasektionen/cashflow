from django.conf.urls import url
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
router.register('expense',  expense_api.ExpenseViewSet, base_name='Expense')
router.register('payment', pay_api.PaymentViewSet, base_name='Payment')
router.register('comment', comment_api.CommentViewSet, base_name='Comment')
router.register('user', user_api.UserViewSet, base_name='User')
router.register('attest', attest_api.AttestViewSet, base_name='Attest')
router.register('accounting', accounting_api.AccountingViewSet, base_name='Accounting')
router.register('file', file_api.FileViewSet, base_name='File')
api_urlpatterns = router.urls

api_urlpatterns.append(url(r'^firebase_instance_id/$', misc_api.set_firebase_instance_id))
api_urlpatterns.append(url(r'^login/(.*)/$', misc_api.login, name='expenses-api-login'))
api_urlpatterns.append(url(r'^logout/$', misc_api.logout))

urlpatterns = [
    url(r'^$', views.index, name='expenses-index'),

    url(r'^user/(?P<username>\w+)/$', views.get_user, name='expenses-user'),
    url(r'^user/(?P<username>\w+)/edit/$', views.edit_user, name='expenses-user-edit'),
    url(r'^user/(?P<username>\w+)/receipts/$', views.get_user_receipts, name='expenses-user-receipts'),

    url(r'^expense/new/$', views.new_expense, name='expenses-expense-new'),
    url(r'^expense/new/binder/(?P<pk>\d+)/$', views.expense_in_binder_alert, name='expenses-expense-new-binder'),
    url(r'^expense/(?P<pk>\d+)/$', views.get_expense, name='expenses-expense'),
    url(r'^expense/(?P<pk>\d+)/edit/$', views.edit_expense, name='expenses-expense-edit'),
    url(r'^expense/(?P<pk>\d+)/verification/edit/$', views.edit_expense_verification, name='expenses-expense-edit-verification'),
    url(r'^expense/(?P<pk>\d+)/delete/$', views.delete_expense, name='expenses-expense-delete'),
    url(r'^expense/(?P<expense_pk>\d+)/comment/$', views.new_comment, name='expenses-expense-comment-new'),
    url(r'^expense/(?P<expense_pk>\d+)/verification/$', views.set_verification, name='expenses-expense-verification'),
    url(r'^expense/(?P<pk>\d+)/confirm/$', views.confirm_expense, name='expenses-expense-confirm'),
    
    url(r'^expense_part/(?P<pk>\d+)/edit/$', views.edit_expense_part, name='expenses-expense_part-edit'),
    url(r'^expense_part/(?P<pk>\d+)/attest/$', views.attest_expense_part, name='expenses-expense_part-attest'),
    
    url(r'^api/payment/new/$', views.api_new_payment, name='expenses-api-payment-new'),
    url(r'^payment/new/$', views.new_payment, name='expenses-payment-new'),
    url(r'^payment/(?P<pk>\d+)/$', views.get_payment, name='expenses-payment'),

    url(r'^confirm/$', views.confirm_overview, name='expenses-action-confirm'),
    url(r'^attest/$', views.attest_overview, name='expenses-action-attest'),
    url(r'^pay/$', views.pay_overview, name='expenses-action-pay'),
    url(r'^accounting/$', views.accounting_overview, name='expenses-action-accounting'),

    url(r'^expenses/$', views.expense_overview, name='expenses-expense-overview'),

    url(r'^admin/$', views.index, name='expenses-admin-index'),
    url(r'^admin/users/$', views.user_list, name='expenses-userlist'),
]

# Code to be run once (https://stackoverflow.com/questions/6791911/execute-code-when-django-starts-once-only)
