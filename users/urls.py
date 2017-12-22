from django.conf.urls import url

import users.views as views

urlpatterns = [
    url(r'^(?P<username>\w+)/$', views.get_user, name='user-show'),
    url(r'^(?P<username>\w+)/edit/$', views.edit_user, name='user-edit'),
    url(r'^(?P<username>\w+)/receipts/$', views.get_user_receipts, name='user-receipts'),
]
