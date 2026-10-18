from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils.module_loading import import_string
from rest_framework import exceptions, generics
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.pagination import DefaultPagination
from core.api.utils import AuthenticatedUserMixin
from core.permissions import get_permission_provider

from ..pictures import ProfilePictureProvider
from .serializers import ProfilePictureQuerySerializer, UserSerializer

profile_picture_provider: ProfilePictureProvider = import_string(
    settings.PROFILE_PICTURE_PROVIDER
)()


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """Retrieves the current user's information based on the authentication credentials."""

    serializer_class = UserSerializer
    http_method_names = ["get", "patch", "options", "head"]

    def get_object(self):
        if not self.request.user.is_authenticated:
            raise exceptions.NotAuthenticated()

        return self.request.user


class ProfilePictureView(generics.ListAPIView):
    """Retrieves profile pictures for a list of usernames."""

    pagination_class = None

    def get(self, request: Request, *args, **kwargs) -> Response:
        query = ProfilePictureQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        usernames = query.validated_data["usernames"]

        keys = {username: f"rfinger:{username}" for username in usernames}
        cached = cache.get_many(keys.values())

        result: dict[str, str | None] = {}
        missing = []
        for username, key in keys.items():
            if key in cached:
                result[username] = cached[key]
            else:
                missing.append(username)

        if missing:
            pictures = profile_picture_provider.get_many(missing)
            fetched = {
                username: str(picture.url) if picture else None
                for username, picture in pictures.items()
            }
            cache.set_many(
                {keys[username]: url for username, url in fetched.items()},
                timeout=settings.PROFILE_PICTURE_CACHE_TIMEOUT * 60 * 60,
            )
            result.update(fetched)

        return Response(result)


class UserListView(APIView, AuthenticatedUserMixin):
    def get(self, request: Request) -> Response:
        permissions = get_permission_provider()

        if not (
            permissions.may_pay(self.current_user)
            or permissions.may_view_all(self.current_user)
        ):
            raise PermissionDenied()

        users = User.objects.order_by("username")
        pagination = DefaultPagination()
        page = pagination.paginate_queryset(users, request, view=self)
        serializer = UserSerializer(page, many=True)

        return pagination.get_paginated_response(serializer.data)


class UserDetailView(APIView, AuthenticatedUserMixin):
    def get(self, request: Request, username: str) -> Response:
        permissions = get_permission_provider()
        if not (
            permissions.may_pay(self.current_user)
            or permissions.may_view_all(self.current_user)
        ):
            raise PermissionDenied()

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise NotFound()
        serializer = UserSerializer(user)
        return Response(serializer.data)
