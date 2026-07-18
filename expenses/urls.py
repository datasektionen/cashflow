from django.urls import re_path

import expenses.views as views

urlpatterns = [
    re_path(r"^new/$", views.new_expense, name="expenses-new"),
    re_path(
        r"^new/confirmation/(?P<pk>\d+)/$",
        views.expense_new_confirmation,
        name="expenses-new-confirmation",
    ),
    re_path(r"^(?P<pk>\d+)/$", views.get_expense, name="expenses-show"),
    re_path(r"^(?P<pk>\d+)/edit/$", views.edit_expense, name="expenses-edit"),
    re_path(r"^(?P<pk>\d+)/delete/$", views.delete_expense, name="expenses-delete"),
    re_path(
        r"^(?P<expense_pk>\d+)/comment/$", views.new_comment, name="expenses-comment"
    ),
    re_path(r"^(?P<pk>\d+)/flag/$", views.flag_expense, name="expenses-flag"),
    re_path(
        r"^api/payment/new/$", views.api_new_payment, name="expenses-api-payment-new"
    ),
    re_path(r"^payment/new/$", views.new_payment, name="expenses-payment-new"),
    re_path(r"^payment/(?P<pk>\d+)/$", views.get_payment, name="expenses-payment"),
]
