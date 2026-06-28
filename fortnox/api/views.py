from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from structlog import get_logger

from fortnox.api.serializers import FortnoxStatusSerializer
from fortnox.models import ServiceAccount

logger = get_logger(__name__)


class ManageFortnoxPermission(permissions.BasePermission):
    """Only users with the `manage-fortnox` Hive permission may manage the integration."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and user.profile.may_manage_fortnox())


def _status_payload() -> dict:
    service_account = ServiceAccount.objects.first()
    is_connected = (
        service_account is not None and service_account.expires_at > timezone.now()
    )
    return {
        "is_connected": is_connected,
        "authenticated_by": (
            service_account.authenticated_by.get_full_name()
            or service_account.authenticated_by.username
            if service_account is not None
            else None
        ),
        "expires_at": (
            service_account.expires_at if service_account is not None else None
        ),
    }


@extend_schema_view(
    get=extend_schema(
        tags=["Fortnox"],
        summary="Get Fortnox connection status",
        responses=FortnoxStatusSerializer,
    )
)
class FortnoxStatusView(APIView):
    permission_classes = [ManageFortnoxPermission]

    def get(self, request):
        return Response(FortnoxStatusSerializer(_status_payload()).data)


@extend_schema_view(
    post=extend_schema(
        tags=["Fortnox"],
        summary="Disconnect the Fortnox service account",
        request=None,
        responses=FortnoxStatusSerializer,
    )
)
class FortnoxDisconnectView(APIView):
    permission_classes = [ManageFortnoxPermission]

    def post(self, request):
        service_account = ServiceAccount.objects.first()
        if service_account is not None:
            token_id = service_account.pk
            service_account.delete()
            logger.warning("fortnox service manually disconnected", token_id=token_id)
        return Response(
            FortnoxStatusSerializer(_status_payload()).data,
            status=status.HTTP_200_OK,
        )
