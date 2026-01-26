from django.urls import re_path, path

import admin.views as views

urlpatterns = [
    re_path(r'^$', views.index, name='admin-index'),

    re_path(r'^confirm/$', views.confirm_overview, name='admin-confirm'),
    re_path(r'^attest/$', views.attest_overview, name='admin-attest'),
    re_path(r'^pay/$', views.pay_overview, name='admin-pay'),
    re_path(r'^account/$', views.account_overview, name='admin-account'),

    # Fortnox integration URLs
    # re_path(r'^auth$', views.fortnox_auth, name='fortnox-auth-get'),
    path('auth/', views.fortnox.get_auth_code, name='fortnox-auth-get'),
    path('auth/complete/', views.fortnox.auth_complete, name='fortnox-auth-complete'),
    # re_path(r'^auth/test$', views.fortnox_auth_test, name='admin-auth-test'),
    # re_path(r'^auth/search$', views.fortnox_auth_search, name='admin-auth-search'),
    # re_path(r'^auth/refresh$', views.fortnox_auth_refresh, name='admin-auth-refresh'),
    # re_path(r'^auth/test/importaccount$', views.fortnox_import_accounts_to_db, name='admin-auth-importaccount'),

    re_path(r'^expense/(?P<pk>\d+)/verification/edit/$', views.edit_expense_verification, name='admin-expense-edit-verification'),
    re_path(r'^expense/(?P<expense_pk>\d+)/verification/$', views.set_verification, name='admin-expense-verification'),
    re_path(r'^expense/(?P<pk>\d+)/confirm/$', views.confirm_expense, name='admin-expense-confirm'),
    re_path(r'^expense/(?P<pk>\d+)/unconfirm/$', views.unconfirm_expense, name='admin-expense-unconfirm'),

    re_path(r'^invoice/(?P<invoice_pk>\d+)/verification/$', views.invoice_set_verification, name='admin-invoice-verification'),

    re_path(r'^expense-part/(?P<pk>\d+)/attest/$', views.attest_expense_part, name='admin-expensepart-attest'),
    re_path(r'^expense-part/(?P<pk>\d+)/unattest/$', views.unattest_expense, name='admin-expense-unattest'),
    re_path(r'^invoice-part/(?P<pk>\d+)/attest/$', views.attest_invoice_part, name='admin-invoicepart-attest'),

    re_path(r'^expenses/$', views.expense_overview, name='admin-expense-overview'),
    re_path(r'^invoices/$', views.invoice_overview, name='admin-invoice-overview'),
    re_path(r'^invoices/(?P<pk>\d+)/pay$', views.invoice_pay, name='admin-invoice-pay'),
    re_path(r'^verifications/$', views.search_verification, name='admin-search-verification'),
    re_path(r'^verifications/search/$', views.search_verification_response, name='admin-search-verification-api'),
    re_path(r'^verifications/list$', views.list_verification, name='admin-list-verification'),
    re_path(r'^users/$', views.user_overview, name='admin-user-overview'),
]
