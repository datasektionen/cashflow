"""cashflow URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.urls import include, re_path, path

from cashflow import settings
from expenses import views as expenses_views
from . import views
from .authviews import login, logout

media_urls = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) if settings.DEBUG else []

app_name = "cashflow"
urlpatterns = [re_path(r'^$', expenses_views.index, name='expenses-index'),
               re_path(r'^accounts/login/$', login, name='login'), re_path(r'^login/$', login, name='login'),
               re_path(r'^logout/', logout, name='logout'), re_path(r'^admin/', include("admin.urls")),
               re_path(r'^expenses/', include("expenses.urls")), re_path(r'^invoices/', include("invoices.urls")),
               re_path(r'^stats/', include("stats.urls")), re_path(r'^users/', include("users.urls")),
               re_path(r'^api/files/', include("file_api.urls")),

               path("api/costcenters/", views.api.CostCenterList.as_view(), name="costcenter-list"),
               path("api/secondarycostcenters/", views.api.SecondaryCostCenterList.as_view(),
                    name="secondarycostcenter-list"),
               path("api/budgetlines/", views.api.BudgetLineList.as_view(), name="budgetline-list"),

               ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + media_urls
