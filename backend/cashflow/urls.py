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

from django.urls import include, re_path, path
from django.views.generic.base import RedirectView

from cashflow import settings

app_name = "cashflow"
urlpatterns = [
    path("api/", include("cashflow.api.urls")),
    path("", include("drf_problems.urls")),
    path("oidc/", include("mozilla_django_oidc.urls")),
    path(
        "login/",
        RedirectView.as_view(url="/oidc/authenticate/", query_string=True),
        name="login",
    ),
]

if settings.FORTNOX_ENABLED:
    urlpatterns += [re_path(r"^fortnox/", include("fortnox.urls"))]
