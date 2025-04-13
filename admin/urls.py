from django.conf.urls import url

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
    url(r'^expense/(?P<pk>\d+)/unconfirm/$', views.unconfirm_expense, name='admin-expense-unconfirm'),

    url(r'^invoice/(?P<invoice_pk>\d+)/verification/$', views.invoice_set_verification, name='admin-invoice-verification'),

    url(r'^expense-part/(?P<pk>\d+)/attest/$', views.attest_expense_part, name='admin-expensepart-attest'),
    url(r'^expense-part/(?P<pk>\d+)/unattest/$', views.unattest_expense, name='admin-expense-unattest'),
    url(r'^invoice-part/(?P<pk>\d+)/attest/$', views.attest_invoice_part, name='admin-invoicepart-attest'),

    url(r'^expenses/$', views.expense_overview, name='admin-expense-overview'),
    url(r'^invoices/$', views.invoice_overview, name='admin-invoice-overview'),
    url(r'^invoices/(?P<pk>\d+)/pay$', views.invoice_pay, name='admin-invoice-pay'),
    url(r'^verifications/$', views.search_verification, name='admin-search-verification'),
    url(r'^verifications/search/$', views.search_verification_response, name='admin-search-verification-api'),
    url(r'^verifications/list$', views.list_verification, name='admin-list-verification'),
    url(r'^users/$', views.user_overview, name='admin-user-overview'),
]
