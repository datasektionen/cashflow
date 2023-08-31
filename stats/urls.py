from django.urls import re_path
from rest_framework.routers import DefaultRouter

import stats.views as views

urlpatterns = [
    re_path(r'^$', views.index, name='stats-index'),
    re_path(r'^summary/$', views.summary, name='stats-summary'),
]
