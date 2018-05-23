from django.conf.urls import url
from rest_framework.routers import DefaultRouter

import file_api.views as views

urlpatterns = [
    url(r'^new/$', views.new_file, name='file_api-new'),
]