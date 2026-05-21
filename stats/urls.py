from django.urls import re_path

import stats.views as views

urlpatterns = [
    re_path(r'^$', views.index, name='stats-index'),
    re_path(r'^monthly/(?P<year>\d+)/$', views.monthly, name='stats-breakdown'),
]
