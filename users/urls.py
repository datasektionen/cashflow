from django.urls import re_path

import users.views as views

urlpatterns = [
    re_path(r'^(?P<username>\w+)/$', views.get_user, name='user-show'),
    re_path(r'^(?P<username>\w+)/edit/$', views.edit_user, name='user-edit'),
    re_path(r'^(?P<username>\w+)/receipts/$', views.get_user_receipts, name='user-receipts'),
]
