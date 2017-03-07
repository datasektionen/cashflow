from django.conf.urls import url
from expenses.expenseviews import expense, expenses
from expenses.misc_views import budget, user_by_username

urlpatterns = [
    url(r'^expense/(?P<expense_id>\d+)/$', expense),
    url(r'^expense/$', expenses),
    url(r'^budget/$',budget),
    url(r'^user/(.*)/', user_by_username)
]
