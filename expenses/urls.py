from django.conf.urls import url

from expenses.views import misc, attest, pay, expense

urlpatterns = [
    #url(r'^expense/(?P<expense_id>\d+)/$', expense.expense),
    #url(r'^expense/new/$', expense.new_expense),
    url(r'^expense/$', expense.ExpenseView.as_view()),
    url(r'^budget/$', misc.budget),
    #url(r'^user/(.*)/expenses/$', expense.expenses_for_person),
    url(r'^user/(.*)/$', misc.user_by_username),
    url(r'^user/$', misc.current_user),
    url(r'^attest/$', attest.attest),
    url(r'^pay/$', pay.pay)
]
