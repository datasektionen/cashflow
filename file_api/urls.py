from django.urls import re_path

import file_api.views as views

urlpatterns = [
    re_path(r'^new/$', views.new_file, name='file_api-new'),
    re_path(r'^(?P<pk>\d+)/delete/$', views.delete_file, name='file_api-delete'),
]
