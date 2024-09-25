from django.conf.urls import url
from rest_framework.routers import DefaultRouter

import invoices.views as views

urlpatterns = [
    url(r'^(?P<pk>\d+)/$', views.get_invoice, name='invoices-show'),
    url(r'^(?P<pk>\d+)/edit/$', views.edit_invoice, name='invoices-edit'),
    url(r'^new/$', views.new_invoice, name='invoices-new'),
    url(r'^new/confirmation/(?P<pk>\d+)/$', views.invoice_new_confirmation, name='invoices-new-confirmation'),
    url(r'^(?P<invoice_pk>\d+)/comment/$', views.new_comment, name='invoices-comment'),
    url(r'^(?P<pk>\d+)/delete/$', views.delete_invoice, name='invoices-delete'),
]
