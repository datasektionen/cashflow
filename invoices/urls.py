from django.conf.urls import url
from rest_framework.routers import DefaultRouter

import invoices.views as views

urlpatterns = [
    url(r'^(?P<pk>\d+)/$', views.get_invoice, name='invoices-show'),
    url(r'^new/$', views.new_invoice, name='invoices-new'),
    url(r'^new/confirmation/(?P<pk>\d+)/$', views.invoice_new_confirmation, name='invoices-new-confirmation'),
    url(r'^(?P<invoice_pk>\d+)/comment/$', views.new_comment, name='invoices-comment'),
]
