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
from .authviews import login, logout

app_name = "cashflow"
urlpatterns = [
    re_path(r"^$", expenses_views.index, name="expenses-index"),
    re_path(r"^claims/", include("expenses.urls")),
    re_path(r"^accounts/login/$", login, name="login"),
    re_path(r"^login/$", login, name="login"),
    re_path(r"^logout/", logout, name="logout"),
    re_path(r"^admin/", include("admin.urls")),
    re_path(r"^invoices/", include("invoices.urls")),
    re_path(r"^stats/", include("stats.urls")),
    re_path(r"^users/", include("users.urls")),
    path("api/", include("cashflow.api.urls")),
    path("", include("drf_problems.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
