from django.conf.urls import include, url
from expenses.expenseviews import expense, expenses

urlpatterns = [
    url(r'^expense/(\d+)/$',expense),
    url(r'^expense/$',expenses),
]
