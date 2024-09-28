from django.conf.urls import url

import stats.views as views

urlpatterns = [
    url(r'^$', views.index, name='stats-index'),
    url(r'^summary/$', views.summary, name='stats-summary'),
    url(r'^monthly/(?P<year>\d+)/$', views.monthly, name='stats-breakdown'),
    url(r'^cost_centres/$', views.cost_centres, name='stats-committees'),
    url(r'^sec_cost_centres/$', views.sec_cost_centres, name='stats-sec_cost_centre'),
    url(r'^budget_lines/$', views.budget_lines, name='stats-budget_lines'),


]
