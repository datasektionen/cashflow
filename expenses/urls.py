from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

import expenses.api_views.accounting as accounting_api
import expenses.api_views.attest as attest_api
import expenses.api_views.comment as comment_api
import expenses.api_views.expense as expense_api
import expenses.api_views.file as file_api
import expenses.api_views.misc as misc_api
import expenses.api_views.pay as pay_api
import expenses.api_views.user as user_api
import expenses.human_views.action as action_views
import expenses.human_views.expense as expense_views
import expenses.human_views.expense_part as expensepart_views
import expenses.human_views.general as general_views
import expenses.human_views.payment as payment_views
import expenses.human_views.user as user_views
from expenses import cron

router = DefaultRouter()
router.register('expense',  expense_api.ExpenseViewSet, base_name='Expense')
router.register('payment', pay_api.PaymentViewSet, base_name='Payment')
router.register('comment', comment_api.CommentViewSet, base_name='Comment')
router.register('user', user_api.UserViewSet, base_name='User')
router.register('attest', attest_api.AttestViewSet, base_name='Attest')
router.register('accounting', accounting_api.AccountingViewSet, base_name='Accounting')
router.register('file', file_api.FileViewSet, base_name='File')
api_urlpatterns = router.urls

api_urlpatterns.append(url(r'^budget/$', misc_api.budget))
api_urlpatterns.append(url(r'^firebase_instance_id/$', misc_api.set_firebase_instance_id))
api_urlpatterns.append(url(r'^committees/$', misc_api.committees))
api_urlpatterns.append(url(r'^cost_centre/(\d+)/$', misc_api.cost_centres))
api_urlpatterns.append(url(r'^login/(.*)/$', misc_api.login, name='expenses-api-login'))
api_urlpatterns.append(url(r'^logout/$', misc_api.logout))


urlpatterns = [
    url(r'^$', general_views.index, name='expenses-index'),
    url(r'^user/(?P<username>\w+)/$', user_views.get_user, name='expenses-user'),
    url(r'^user/(?P<username>\w+)/edit/$', user_views.edit_user, name='expenses-user-edit'),

    url(r'^expense/new/$', expense_views.new_expense, name='expenses-expense-new'),
    url(r'^expense/(?P<pk>\d+)/$', expense_views.get_expense, name='expenses-expense'),
    url(r'^expense/(?P<expense_pk>\d+)/comment/$', expense_views.new_comment, name='expenses-expense-comment-new'),
    url(r'^expense/(?P<expense_pk>\d+)/verification/$', expense_views.set_verification, name='expenses-expense'
                                                                                             '-verification'),

    url(r'^expense_part/(?P<pk>\d+)/edit/$', expensepart_views.edit_expense_part, name='expenses-expense_part-edit'),
    url(r'^expense_part/(?P<pk>\d+)/attest/$', expensepart_views.attest_expense_part, name='expenses-expense_part'
                                                                                           '-attest'),

    url(r'^payment/new/$', payment_views.new_payment, name='expenses-payment-new'),
    url(r'^payment/(?P<pk>\d+)/$', payment_views.get_payment, name='expenses-payment'),

    url(r'^attest/$', action_views.attest_overview, name='expenses-action-attest'),
    url(r'^pay/$', action_views.pay_overview, name='expenses-action-pay'),
    url(r'^accounting/$', action_views.accounting_overview, name='expenses-action-accounting'),
    url(r'^api/', include(api_urlpatterns)),
]

# Code to be run once (https://stackoverflow.com/questions/6791911/execute-code-when-django-starts-once-only)

cron.start()
