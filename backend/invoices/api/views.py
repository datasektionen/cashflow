import json
from typing import Any, cast

from django.db import transaction
from django.http import QueryDict
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from structlog import get_logger

from core.api.filters import apply_invoice_filters
from core.api.problems import (
    AccountingPermissionDeniedProblem,
    AlreadyConfirmedProblem,
    AlreadyPaidProblem,
    ConfirmationPermissionDeniedProblem,
    DeletionPermissionDeniedProblem,
    FileRequiredProblem,
    MismatchedTotalAmountProblem,
    NoAccountingMethodProblem,
    NotConfirmedProblem,
    NotPayableProblem,
    PartInvalidJSONProblem,
    PartRequiredProblem,
    PaymentPermissionDeniedProblem,
    UnconfirmationPermissionDeniedProblem,
    UpdatePermissionDeniedProblem,
)
from core.api.serializers import ClaimPartSerializer, CommentSerializer
from core.api.utils import AuthenticatedUserMixin
from core.exceptions import (
    AlreadyAccountedError,
    CashflowVerificationMissingError,
    DuplicateConfirmationError,
    FortnoxRecordMissingError,
    MismatchedTotalAmountError,
    NoAccountingMethodError,
    NotConfirmedError,
    UnauthorizedAccountingError,
    UnauthorizedConfirmationError,
    UnauthorizedUnconfirmationError,
)
from core.files import normalize_upload
from core.models import Claim, ClaimPart, Comment, File
from core.permissions import get_permission_provider
from fortnox import VoucherRow
from fortnox.api.problems import (
    AlreadyAccountedProblem,
    CashflowVerificationMissingProblem,
    FortnoxRecordMissingProblem,
    FortnoxServiceNotAvailableProblem,
)
from notifications import get_notification_provider

from .serializers import (
    InvoiceAccountSerializer,
    InvoiceSerializer,
)

logger = get_logger(__name__)


class InvoiceViewSet(viewsets.ModelViewSet, AuthenticatedUserMixin):
    # Invoices are addressed by their InvoiceData id, see Claim.data_id
    lookup_field = "invoice_data_id"
    lookup_url_kwarg = "pk"
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = [
        *(m for m in viewsets.ModelViewSet.http_method_names if m != "put"),
        "query",
    ]

    def create(self, request: Request, *args, **kwargs) -> Response:

        files = request.FILES.getlist("files")
        if not files:
            raise FileRequiredProblem()
        data = cast(QueryDict, request.data).dict()
        try:
            parts_raw = cast("str | None", data.get("parts"))
            if parts_raw is None:
                raise PartRequiredProblem()
            data["parts"] = json.loads(parts_raw)
        except json.JSONDecodeError, TypeError:
            raise PartInvalidJSONProblem(
                detail="There was a problem decoding the parts field. Invoice parts should be submitted as a JSON encoded array."
            )
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        parts_data = cast("list[dict[str, Any]]", data["parts"])
        with transaction.atomic():
            invoice = serializer.save(owner=self.current_user.profile)
            for part in parts_data:
                ClaimPart.objects.create(claim=invoice, **part)
            for f in files:
                File.objects.create(claim=invoice, file=normalize_upload(f))

        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        invoice = self.get_object()
        if invoice.payed_at is not None:
            raise DeletionPermissionDeniedProblem()
        if not (
            get_permission_provider().may_delete(self.current_user)
            or invoice.owner == self.current_user.profile
        ):
            raise DeletionPermissionDeniedProblem()
        return super().destroy(request, *args, **kwargs)

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        invoice = self.get_object()
        assert invoice.invoice_data is not None
        if invoice.invoice_data.paid_at is not None:
            raise UpdatePermissionDeniedProblem()
        if not invoice.owner == self.current_user.profile:
            raise UpdatePermissionDeniedProblem()

        data = (
            request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
        )

        # Allow passing IDs for files to be removed
        if deletes := data.pop("delete_files", None):
            try:
                deletes_data: list[int] = json.loads(deletes)
                invoice.file_set.filter(id__in=deletes_data).delete()
            except json.JSONDecodeError:
                raise PartInvalidJSONProblem()

        parts_data = data.pop("parts", None)
        if isinstance(parts_data, str):
            try:
                parts_data = json.loads(parts_data)
            except json.JSONDecodeError:
                raise PartInvalidJSONProblem()
        if parts_data is not None:
            if not parts_data:
                raise PartRequiredProblem()
            parts_serializer = ClaimPartSerializer(data=parts_data, many=True)
            parts_serializer.is_valid(raise_exception=True)
            parts_data = parts_serializer.validated_data

        files = request.FILES.getlist("files")

        serializer = self.get_serializer(invoice, data=data, partial=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            serializer.save()
            if parts_data is not None:
                invoice.parts.all().delete()
                for part in parts_data:
                    ClaimPart.objects.create(claim=invoice, **part)
            for f in files:
                File.objects.create(claim=invoice, file=normalize_upload(f))

        invoice.refresh_from_db()
        return Response(
            InvoiceSerializer(invoice, context=self.get_serializer_context()).data
        )

    def get_queryset(self):
        queryset = (
            Claim.objects.invoices()
            .select_related(
                "owner__user",
                "invoice_data__paid_by__user",
            )
            .prefetch_related(
                "file_set",
                "parts__attested_by__user",
                "comment_set__author__user",
            )
            .viewable_by(self.current_user)
            .with_total()
        )
        return apply_invoice_filters(
            queryset, self.request.GET, self.current_user
        ).distinct()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Recommendations require a GOrdian/Fortnox lookup per part, so only
        # compute them for single-invoice reads (e.g. the accounting page),
        # never for list responses.
        context["include_recommendations"] = self.action == "retrieve"
        return context

    @action(detail=False, methods=["POST", "QUERY"], url_path="search")  # type: ignore[list-item]
    def search(self, request: Request) -> Response:
        assert isinstance(request.data, dict)
        query = request.data.get("query") or {}
        invoices = self.get_queryset().search(**query)
        page = self.paginate_queryset(invoices)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(InvoiceSerializer(invoices, many=True).data)

    @action(detail=True, methods=["post"], url_path="comments")
    def comment(self, request: Request, pk=None) -> Response:
        invoice = self.get_object()
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = Comment.objects.create(
            content=serializer.validated_data["content"],
            claim=invoice,
            author=self.current_user.profile,
        )

        get_notification_provider().on_comment(invoice, comment)

        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["POST"])
    def confirm(self, request: Request, pk=None) -> Response:
        with transaction.atomic():
            invoice = Claim.objects.select_for_update().get(invoice_data_id=pk)
            try:
                invoice.confirm(self.current_user)
            except UnauthorizedConfirmationError as e:
                raise ConfirmationPermissionDeniedProblem(
                    detail="You are not authorized to confirm this invoice."
                ) from e
            except DuplicateConfirmationError as e:
                raise AlreadyConfirmedProblem(
                    detail="This invoice has already been confirmed."
                ) from e

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["POST"])
    def unconfirm(self, request: Request, pk=None) -> Response:
        with transaction.atomic():
            invoice = Claim.objects.select_for_update().get(invoice_data_id=pk)
            try:
                invoice.unconfirm(self.current_user)
            except UnauthorizedUnconfirmationError as e:
                raise UnconfirmationPermissionDeniedProblem() from e
            except NotConfirmedError as e:
                raise NotConfirmedProblem() from e
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["POST"])
    def pay(self, request: Request, pk=None) -> Response:
        if not get_permission_provider().may_pay(self.current_user):
            raise PaymentPermissionDeniedProblem()

        with transaction.atomic():
            invoice = get_object_or_404(
                Claim.objects.select_for_update(), invoice_data_id=pk
            )
            assert invoice.invoice_data is not None
            if invoice.invoice_data.paid_by is not None:
                raise AlreadyPaidProblem()
            if not invoice.is_payable():
                raise NotPayableProblem()
            invoice.pay(self.current_user)

        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"])
    def account(self, request: Request, pk=None) -> Response:
        serializer = InvoiceAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        voucher_number = serializer.validated_data.get("voucher_number")
        voucher_rows_data = serializer.validated_data.get("voucher_rows", [])

        fortnox_client = None
        if not voucher_number:
            fortnox_client = getattr(request, "fortnox_service", None)
            if fortnox_client is None:
                raise FortnoxServiceNotAvailableProblem()
            if not voucher_rows_data:
                raise PartRequiredProblem()

        voucher_rows = [
            VoucherRow(
                Account=row["account"],
                CostCenter=(
                    str(row["cost_centre"])
                    if row.get("cost_centre") is not None
                    else None
                ),
                Debit=float(row["debit"]) if row.get("debit") is not None else None,
                Credit=float(row["credit"]) if row.get("credit") is not None else None,
            )
            for row in voucher_rows_data
        ]

        with transaction.atomic():
            invoice = Claim.objects.select_for_update().get(invoice_data_id=pk)
            try:
                invoice.account(
                    self.current_user,
                    fortnox_client=fortnox_client,
                    voucher_rows=voucher_rows,
                    voucher_number=voucher_number,
                )
            except UnauthorizedAccountingError as e:
                raise AccountingPermissionDeniedProblem() from e
            except AlreadyAccountedError as e:
                raise AlreadyAccountedProblem() from e
            except FortnoxRecordMissingError as e:
                raise FortnoxRecordMissingProblem() from e
            except CashflowVerificationMissingError as e:
                raise CashflowVerificationMissingProblem() from e
            except MismatchedTotalAmountError as e:
                raise MismatchedTotalAmountProblem() from e
            except NoAccountingMethodError as e:
                raise NoAccountingMethodProblem() from e
        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_200_OK)
