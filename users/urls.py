from django.urls import re_path, path

import users.views as views

urlpatterns = [
    path("me/", views.CurrentUserView.as_view(), name="current-user"),
    re_path(r"^(?P<username>\w+)/$", views.get_user, name="user-show"),
    re_path(r"^(?P<username>\w+)/edit/$", views.edit_user, name="user-edit"),
    re_path(
        r"^(?P<username>\w+)/receipts/$", views.get_user_receipts, name="user-receipts"
    ),
]