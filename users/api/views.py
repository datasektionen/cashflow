from django.conf import settings
from drf_spectacular.utils import extend_schema_view, extend_schema, inline_serializer
from rest_framework import generics, exceptions, status, serializers
from rest_framework.response import Response
from django.utils.module_loading import import_string

from .serializers import UserSerializer, ProfilePictureQuerySerializer
from ..pictures import ProfilePictureProvider

profile_picture_provider: ProfilePictureProvider = import_string(
    settings.PROFILE_PICTURE_PROVIDER
)()


@extend_schema_view(
    get=extend_schema(
        summary="Get current user",
        operation_id="get_current_user",
        tags=["Users"],
    )
)
class CurrentUserView(generics.RetrieveAPIView):
    """Retrieves the current user's information based on the authentication credentials."""

    serializer_class = UserSerializer

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

        pictures = profile_picture_provider.get_many(usernames)
        return Response(
            {
                username: str(picture.url) if picture else None
                for username, picture in pictures.items()
            }
        )
