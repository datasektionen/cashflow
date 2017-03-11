from django.conf.urls import url
from expenses import expenseviews
from expenses import misc_views

urlpatterns = [
    url(r'^expense/(?P<expense_id>\d+)/$', expenseviews.expense),
    url(r'^expense/$', expenseviews.expenses),
    url(r'^budget/$', misc_views.budget),
    url(r'^user/(.*)/$', misc_views.user_by_username),
    url(r'^user/(.*)/expenses/$', misc_views.user_by_username),
    url(r'^user/$', misc_views.current_user)
]

