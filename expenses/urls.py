from django.conf.urls import url
from expenses.expenseviews import expense, expenses

urlpatterns = [
    url(r'^expense/(?P<expense_id>\d+)/$', expense),
    url(r'^expense/$', expenses),
]
