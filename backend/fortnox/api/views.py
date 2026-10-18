from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from structlog import get_logger

from cashflow.utils import list_active_accounts, list_active_cost_centers
from fortnox.api.problems import FortnoxServiceNotAvailableProblem
from fortnox.api.serializers import (
    FortnoxAccountSerializer,
    FortnoxCostCentreSerializer,
    FortnoxStatusSerializer,
)
from fortnox.models import ServiceAccount

logger = get_logger(__name__)


class ManageFortnoxPermission(permissions.BasePermission):
    """Only users with the `manage-fortnox` Hive permission may manage the integration."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and user.profile.may_manage_fortnox())


class AccountingPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user.is_authenticated
            and (user.profile.may_account_some() or user.profile.may_view_all())
        )


class ViewFortnoxStatusPermission(permissions.BasePermission):
    """Users who manage Fortnox or have `view_all` may read the connection status."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user.is_authenticated
            and (user.profile.may_manage_fortnox() or user.profile.may_view_all())
        )


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


class FortnoxStatusView(APIView):
    permission_classes = [ViewFortnoxStatusPermission]

    def get(self, request):
        return Response(FortnoxStatusSerializer(_status_payload()).data)


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


class FortnoxAccountList(APIView):
    permission_classes = [AccountingPermission]

    def get(self, request):
        if getattr(request, "fortnox_service", None) is None:
            raise FortnoxServiceNotAvailableProblem()
        accounts = list_active_accounts(request)
        return Response(FortnoxAccountSerializer(accounts, many=True).data)


class FortnoxCostCentreList(APIView):
    permission_classes = [AccountingPermission]

    def get(self, request):
        if getattr(request, "fortnox_service", None) is None:
            raise FortnoxServiceNotAvailableProblem()
        cost_centres = list_active_cost_centers(request)
        return Response(FortnoxCostCentreSerializer(cost_centres, many=True).data)
