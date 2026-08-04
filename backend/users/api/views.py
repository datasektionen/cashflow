from django.conf import settings
from django.core.cache import cache
from django.utils.module_loading import import_string
from drf_spectacular.utils import extend_schema_view, extend_schema, inline_serializer
from rest_framework import generics, exceptions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from django.contrib.auth.models import User
from core.api.pagination import DefaultPagination

from .serializers import UserSerializer, ProfilePictureQuerySerializer
from ..pictures import ProfilePictureProvider
from core.permissions import get_permission_provider
from core.api.utils import AuthenticatedUserMixin

profile_picture_provider: ProfilePictureProvider = import_string(
    settings.PROFILE_PICTURE_PROVIDER
)()


@extend_schema_view(
    get=extend_schema(
        summary="Get current user",
        operation_id="get_current_user",
        tags=["Users"],
    ),
    patch=extend_schema(
        summary="Update current user",
        description=(
            "Updates the current user's bank information. Identity fields "
            "come from the SSO and are read-only."
        ),
        operation_id="update_current_user",
        tags=["Users"],
    ),
    put=extend_schema(exclude=True),
)
class CurrentUserView(generics.RetrieveUpdateAPIView):
    """Retrieves the current user's information based on the authentication credentials."""

    serializer_class = UserSerializer
    http_method_names = ["get", "patch", "options", "head"]

    def get_object(self):
        if not self.request.user.is_authenticated:
            raise exceptions.NotAuthenticated()

        return self.request.user


@extend_schema(
    tags=["Users"],
    summary="Get profile pictures",
    description="Retrieves profile pictures for one or more users. Does not paginate the response.",
    parameters=[ProfilePictureQuerySerializer],
    responses={
        status.HTTP_200_OK: inline_serializer(
            name="ProfilePictureResponse",
            fields={"username": serializers.URLField()},
        ),
    },
    operation_id="get_profile_pictures",
)
class ProfilePictureView(generics.ListAPIView):
    """Retrieves profile pictures for a list of usernames."""

    pagination_class = None

    def get(self, request, *args, **kwargs):
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


@extend_schema(
    summary="List users",
    tags=["Users"],
    operation_id="list_users",
    description="Lists all users.",
)
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
