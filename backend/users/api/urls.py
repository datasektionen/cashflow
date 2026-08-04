from django.urls import path

from . import views

urlpatterns = [
    path("", views.UserListView.as_view(), name="users_list"),
    path("me/", views.CurrentUserView.as_view(), name="current-user"),
    path(
        "profile-pictures/", views.ProfilePictureView.as_view(), name="profile-pictures"
    ),
]
