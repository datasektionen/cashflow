from django.conf.urls import url
from rest_framework.routers import DefaultRouter

import admin.views as views

urlpatterns = [
    url(r'^$', views.index, name='admin-index'),

    url(r'^confirm/$', views.confirm_overview, name='admin-confirm'),
    url(r'^attest/$', views.attest_overview, name='admin-attest'),
    url(r'^pay/$', views.pay_overview, name='admin-pay'),
    url(r'^account/$', views.account_overview, name='admin-account'),

    url(r'^expense/(?P<pk>\d+)/verification/edit/$', views.edit_expense_verification, name='admin-expense-edit-verification'),
    url(r'^expense/(?P<expense_pk>\d+)/verification/$', views.set_verification, name='admin-expense-verification'),
    url(r'^expense/(?P<pk>\d+)/confirm/$', views.confirm_expense, name='admin-expense-confirm'),

    url(r'^expense-part/(?P<pk>\d+)/attest/$', views.attest_expense_part, name='admin-expensepart-attest'),
    url(r'^invoice-part/(?P<pk>\d+)/attest/$', views.attest_invoice_part, name='admin-invoicepart-attest'),

    url(r'^expenses/$', views.expense_overview, name='admin-expense-overview'),
    url(r'^invoices/$', views.invoice_overview, name='admin-invoice-overview'),
    url(r'^verifications/$', views.search_verification, name='admin-search-verification'),
    url(r'^verifications/search/$', views.search_verification_response, name='admin-search-verification-api'),
    url(r'^users/$', views.user_overview, name='admin-user-overview'),
]