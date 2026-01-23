from django.urls import re_path

import stats.views as views

urlpatterns = [
    re_path(r'^$', views.index, name='stats-index'),
    re_path(r'^summary/$', views.summary, name='stats-summary'),
    re_path(r'^monthly/(?P<year>\d+)/$', views.monthly, name='stats-breakdown'),
    re_path(r'^cost_centres/$', views.cost_centres, name='stats-committees'),
    re_path(r'^sec_cost_centres/$', views.sec_cost_centres, name='stats-sec_cost_centre'),
    re_path(r'^budget_lines/$', views.budget_lines, name='stats-budget_lines'),
]
