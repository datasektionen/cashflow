from django.conf.urls import url

import stats.views as views

urlpatterns = [
    url(r'^$', views.index, name='stats-index'),
    url(r'^summary/$', views.summary, name='stats-summary'),
    url(r'^monthly/(?P<year>\d+)/$', views.monthly, name='stats-breakdown'),
]
