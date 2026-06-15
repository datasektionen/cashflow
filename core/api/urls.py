from django.urls import path

from .views import PendingPaymentsList

urlpatterns = [
    path("payments/pending/", PendingPaymentsList.as_view()),
]
