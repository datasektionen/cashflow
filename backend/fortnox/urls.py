from django.urls import path

from fortnox import views

urlpatterns = [
    path("auth/", views.get_auth_code, name="fortnox-auth-get"),
    path("auth/complete/", views.auth_complete, name="fortnox-auth-complete"),
]
