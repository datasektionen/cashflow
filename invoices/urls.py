from django.conf.urls import url
from rest_framework.routers import DefaultRouter

import invoices.views as views

urlpatterns = [
    url(r'^new/$', views.new_invoice, name='invoices-new'),
]
