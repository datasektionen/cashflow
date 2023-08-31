"""cashflow URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  re_path(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  re_path(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  re_path(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include
from django.urls import re_path
from django.conf.urls.static import static
from django.contrib import admin

from cashflow import settings
from expenses import views
from .authviews import login, login_with_token, logout


pat, app_namespace, _ = admin.site.urls

urlpatterns = [
    re_path(r'^$', views.index, name='expenses-index'),
    re_path(r'^login/$', login, name='login'),
    re_path(r'^login/(?P<token>.+)/$', login_with_token, name='login_with_token'),
    re_path(r'^logout/', logout, name='logout'),
    re_path(r'^admin/', include("admin.urls")),
    re_path(r'^admin/django/', include((pat, app_namespace), app_namespace)),
    re_path(r'^expenses/', include("expenses.urls")),
    re_path(r'^invoices/', include("invoices.urls")),
    re_path(r'^stats/', include("stats.urls")),
    re_path(r'^users/', include("users.urls")),
    re_path(r'^api/files/', include("file_api.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
