from django.conf.urls import url
from expenses import expenseviews, misc_views, attestviews, payviews

urlpatterns = [
    url(r'^expense/(?P<expense_id>\d+)/$', expenseviews.expense),
    url(r'^expense/new/$',expenseviews.new_expense),
    url(r'^expense/$', expenseviews.expenses),
    url(r'^budget/$', misc_views.budget),
    url(r'^user/(.*)/expenses/$', expenseviews.expenses_for_person),
    url(r'^user/(.*)/$', misc_views.user_by_username),
    url(r'^user/$', misc_views.current_user),
    url(r'^attest/$',attestviews.attest),
    url(r'^pay/$',payviews.pay)
]

