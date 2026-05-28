from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import generics, exceptions

from .serializers import UserSerializer


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
