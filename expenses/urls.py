from django.urls import re_path

import expenses.views as views

urlpatterns = [
    re_path(r"^new/$", views.new_expense, name="claims-new"),
    re_path(
        r"^new/confirmation/(?P<pk>\d+)/$",
        views.expense_new_confirmation,
        name="claims-new-confirmation",
    ),
    re_path(r"^(?P<pk>\d+)/$", views.get_expense, name="claims-show"),
    re_path(r"^(?P<pk>\d+)/edit/$", views.edit_expense, name="claims-edit"),
    re_path(r"^(?P<pk>\d+)/delete/$", views.delete_expense, name="claims-delete"),
    re_path(
        r"^(?P<expense_pk>\d+)/comment/$", views.new_comment, name="claims-comment"
    ),
    re_path(r"^(?P<pk>\d+)/flag/$", views.flag_expense, name="claims-flag"),
    re_path(
        r"^api/payment/new/$", views.api_new_payment, name="claims-api-payment-new"
    ),
    re_path(r"^payment/new/$", views.new_payment, name="claims-payment-new"),
    re_path(r"^payment/(?P<pk>\d+)/$", views.get_payment, name="claims-payment"),
]
