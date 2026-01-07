from django.urls import re_path
from rest_framework.routers import DefaultRouter

import invoices.views as views

urlpatterns = [
    re_path(r'^(?P<pk>\d+)/$', views.get_invoice, name='invoices-show'),
    re_path(r'^(?P<pk>\d+)/edit/$', views.edit_invoice, name='invoices-edit'),
    re_path(r'^new/$', views.new_invoice, name='invoices-new'),
    re_path(r'^new/confirmation/(?P<pk>\d+)/$', views.invoice_new_confirmation, name='invoices-new-confirmation'),
    re_path(r'^(?P<invoice_pk>\d+)/comment/$', views.new_comment, name='invoices-comment'),
    re_path(r'^(?P<pk>\d+)/delete/$', views.delete_invoice, name='invoices-delete'),
]
