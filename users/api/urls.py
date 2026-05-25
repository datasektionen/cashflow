from django.urls import path

from . import views

urlpatterns = [
    path("me/", views.CurrentUserView.as_view(), name="current-user"),
]
