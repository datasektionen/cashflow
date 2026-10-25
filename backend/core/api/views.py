from typing import TypedDict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import CharField, Q, Value
from django.db.models.aggregates import Count, Sum
from django.db.models.functions import Cast, Coalesce, Concat
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from structlog import get_logger

from core.api.filters import ClaimFilter
from core.api.pagination import DefaultPagination
from core.api.problems import (
    AlreadyReimbursedProblem,
    AttestationPermissionDeniedProblem,
    IsFlaggedProblem,
    MultipleReceiversProblem,
    PaymentPermissionDeniedProblem,
)
from core.api.serializers import (
    ClaimPartSerializer,
    ClaimSerializer,
    PaymentCreateSerializer,
    PendingPaymentsSerializer,
    VoucherSeriesSerializer,
)
from core.api.utils import AuthenticatedUserMixin
from core.exceptions import (
    FlaggedAttestationError,
    SelfAttestationError,
    UnauthorizedAttestationError,
)
from core.models import Claim, ClaimPart, ClaimQuerySet, Comment, Profile
from core.permissions import get_permission_provider
from core.search import claim_search
from expenses.api.serializers import PaymentSerializer
from expenses.models import Payment
from fortnox import FortnoxNotFound, FortnoxRequest, FortnoxServiceNotAvailableProblem
from notifications import get_notification_provider

UserModel = get_user_model()
logger = get_logger(__name__)


class ClaimsList(ListAPIView, AuthenticatedUserMixin):
    """Lists both expenses and invoices."""

    serializer_class = ClaimSerializer
    pagination_class = DefaultPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ClaimFilter

    def get_queryset(self) -> ClaimQuerySet:
        return (
            Claim.objects.select_related("owner__user", "expense_data", "invoice_data")
            .prefetch_related("parts__attested_by__user")
            .viewable_by(self.current_user)
            .annotate(
                date=Coalesce(
                    "expense_data__expense_date",
                    "invoice_data__invoice_date",
                    "invoice_data__paid_at",
                )
            )
            .with_total()
            .distinct()
        )


class ClaimPartAttestView(GenericAPIView[ClaimPart], AuthenticatedUserMixin):
    serializer_class = ClaimPartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ClaimPart.objects.filter(
            claim__in=Claim.objects.viewable_by(self.current_user)
        ).select_related("claim__expense_data", "claim__owner")

    def post(self, request: Request, pk: int) -> Response:
        with transaction.atomic():
            part = self.get_object()
            part = (
                ClaimPart.objects.select_for_update(of=("self",))
                .select_related("claim__expense_data", "claim__owner")
                .get(pk=part.pk)
            )
            try:
                part.attest(self.current_user)
            except FlaggedAttestationError as e:
                raise IsFlaggedProblem(
                    detail="This expense is flagged and cannot be attested."
                ) from e
            except UnauthorizedAttestationError as e:
                raise AttestationPermissionDeniedProblem(
                    detail=f"You do not have permission to attest this part, {part.cost_centre} is not a cost centre for which you can attest."
                ) from e
            except SelfAttestationError as e:
                raise AttestationPermissionDeniedProblem(
                    detail="You do not have permission to attest this part, you cannot attest your own expenses."
                ) from e

        return Response(status=status.HTTP_204_NO_CONTENT)


class ClaimPartUnattestView(GenericAPIView[ClaimPart], AuthenticatedUserMixin):
    serializer_class = ClaimPartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ClaimPart.objects.filter(
            claim__in=Claim.objects.viewable_by(self.current_user)
        ).select_related("claim")

    def post(self, request: Request, pk: int) -> Response:
        with transaction.atomic():
            part = self.get_object()
            part = (
                ClaimPart.objects.select_for_update()
                .select_related("claim")
                .get(pk=part.pk)
            )
            try:
                part.unattest(self.current_user)
            except UnauthorizedAttestationError as e:
                raise AttestationPermissionDeniedProblem(
                    detail=f"You do not have permission to unattest this part, {part.cost_centre} is not a cost centre for which you can attest."
                ) from e

        return Response(status=status.HTTP_204_NO_CONTENT)


class PaymentViewSet(viewsets.GenericViewSet, AuthenticatedUserMixin):
    """
    Payments (expense reimbursements).

    A payment reimburses one member for a batch of their expenses. Invoice
    payments are a different flow (a per-invoice action on the invoice) and are
    intentionally not handled here — see ``Invoice.pay``.
    """

    pagination_class = DefaultPagination

    def get_serializer_class(self):
        if self.action == "create":
            return PaymentCreateSerializer
        if self.action == "pending":
            return PendingPaymentsSerializer
        return PaymentSerializer

    def list(self, request: Request) -> Response:
        if not get_permission_provider().may_pay(
            self.current_user
        ) and not get_permission_provider().may_view_all(self.current_user):
            return Response(status=status.HTTP_403_FORBIDDEN)

        payments = Payment.objects.all().order_by("-date")

        if tag := request.query_params.get("tag"):
            payments = payments.annotate(
                tag_text=Concat(
                    Value(settings.PAYMENT_TAG_PREFIX),
                    Cast("pk", CharField()),
                )
            ).filter(tag_text__icontains=tag)

        page = self.paginate_queryset(payments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)

    def create(self, request: Request) -> Response:
        if not get_permission_provider().may_pay(self.current_user):
            raise PaymentPermissionDeniedProblem()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expenses: list[Claim] = serializer.validated_data["expenses"]

        if not all(
            expense.expense_data and expense.expense_data.reimbursement is None
            for expense in expenses
        ):
            raise AlreadyReimbursedProblem(
                detail="One or more expenses are already reimbursed."
            )

        receivers = {expense.owner_id for expense in expenses}
        if len(receivers) > 1:
            raise MultipleReceiversProblem()

        receiver = expenses[0].owner

        with transaction.atomic():
            payment = Payment.objects.create(
                payer=self.current_user.profile, receiver=receiver
            )
            for expense in expenses:
                assert expense.expense_data is not None
                expense.expense_data.reimbursement = payment
                expense.expense_data.save(update_fields=["reimbursement"])
                expense.save(update_fields=["expense_data"])
                comment = Comment.objects.create(
                    author=self.current_user.profile,
                    claim=expense,
                    content=f"Betalade ut i betalning {payment.id}",
                )

                get_notification_provider().on_comment(expense, comment)

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["GET"])
    def pending(self, request: Request) -> Response:
        if not get_permission_provider().may_pay(
            self.current_user
        ) and not get_permission_provider().may_view_all(self.current_user):
            raise PermissionDenied()

        payable = Q(
            claim__expense_data__reimbursement__isnull=True,
            claim__expense_data__confirmed_by__isnull=False,
            claim__part__attested_by__isnull=False,
        )
        queryset = (
            Profile.objects.annotate(
                count=Count("claim", filter=payable, distinct=True)
            )
            .annotate(total=Sum("claim__part__amount", filter=payable))
            .filter(count__gt=0)
            .filter(total__isnull=False)
            .order_by("-total")
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ActionSummary(GenericAPIView, AuthenticatedUserMixin):
    def get(self, request: Request):
        user = self.current_user
        expenses = Claim.objects.expenses()
        invoices = Claim.objects.invoices()
        return Response(
            {
                "expenses": {
                    "attestable": expenses.attestable_for(user).count(),
                    "confirmable": expenses.confirmable_for(user).count(),
                    "accountable": expenses.accountable_for(user).count(),
                    "payable": expenses.payable_for(user).count(),
                },
                "invoices": {
                    "attestable": invoices.attestable_for(user).count(),
                    "accountable": invoices.accountable_for(user).count(),
                    "payable": invoices.payable_for(user).count(),
                },
            }
        )


def _counts_by_cost_centre(qs: ClaimQuerySet) -> list[dict[str, object]]:
    """Counts claims grouped by cost centre, sorted by descending count."""
    return [
        {"cost_centre": row["part__cost_centre"], "count": row["count"]}
        for row in qs.order_by()
        .values("part__cost_centre")
        .annotate(count=Count("id", distinct=True))
        .order_by("-count")
    ]


class _OwnerCount(TypedDict):
    username: str
    first_name: str
    last_name: str
    count: int


def _counts_by_owner(qs: ClaimQuerySet) -> list[_OwnerCount]:
    """Counts claims grouped by the owning user, sorted by descending count.

    Each claim has a single owner, so counts sum to the overall total.
    """
    return [
        {
            "username": row["owner__user__username"],
            "first_name": row["owner__user__first_name"],
            "last_name": row["owner__user__last_name"],
            "count": row["count"],
        }
        for row in qs.order_by()
        .values(
            "owner__user__username",
            "owner__user__first_name",
            "owner__user__last_name",
        )
        .annotate(count=Count("id", distinct=True))
        .order_by("-count")
    ]


class ActionOverview(GenericAPIView, AuthenticatedUserMixin):
    def get(self, request: Request):
        user = self.current_user
        return Response(
            {
                "attest": _counts_by_cost_centre(Claim.objects.attestable_for(user)),
                "account": _counts_by_cost_centre(Claim.objects.accountable_for(user)),
                "confirm": _counts_by_cost_centre(Claim.objects.confirmable_for(user)),
                "pay": _counts_by_owner(Claim.objects.payable_for(user)),
            }
        )


class VoucherSeriesList(GenericAPIView):
    def get_serializer_class(self):
        return VoucherSeriesSerializer

    def get(self, request: FortnoxRequest):

        series: list[dict[str, str | None]] = []

        include_fortnox = request.GET.get("include_fortnox", "true").lower() != "false"

        if request.fortnox_service is not None and include_fortnox:
            by_code: dict[str, str | None] = {}
            try:
                for vs in request.fortnox_service.list_voucher_series():
                    if vs.Code.isalpha() and len(vs.Code) == 1:
                        by_code.setdefault(vs.Code, vs.Description)
                series = [
                    {"code": code, "description": description}
                    for code, description in by_code.items()
                ]
            except FortnoxNotFound as e:
                # Indicates the fortnox integration is disconnected
                raise FortnoxServiceNotAvailableProblem(
                    detail="Fetching voucher series from Fortnox failed, this most likely means the integration "
                    "is unavailable."
                ) from e

        # Find voucher series from existing expenses and invoices
        verifications = (
            Claim.objects.exclude(verification="")
            .values_list("verification", flat=True)
            .distinct()
        )
        codes = {v[0].upper() for v in verifications if v[0].isalpha()}

        known = {sc["code"] for sc in series}
        inactive: list[dict[str, str | None]] = [
            {"code": code} for code in sorted(codes - known)
        ]
        series += inactive

        page: list[dict[str, str | None]] | None = self.paginate_queryset(series)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(VoucherSeriesSerializer(series, many=True).data)
