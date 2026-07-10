import json
from typing import Any, cast

from django.contrib.auth.models import User
from django.db import transaction
from django.http import QueryDict
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from structlog import get_logger

from core.api.filters import Filter, apply_invoice_filters, OPENAPI_PARAMS
from core.api.openapi import problem, problems
from core.api.serializers import CommentCreateSerializer, CommentSerializer
from core.api.utils import AuthenticatedUserMixin
from core.files import normalize_upload
from expenses.models import File, Comment
from .problems import (
    InvalidInvoiceDateError,
    InvalidDueDateError,
    VerificationRequiredError,
)
from core.api.problems import (
    PartInvalidJSONProblem,
    FileRequiredProblem,
    PartRequiredProblem,
    AttestationPermissionDeniedProblem,
    EmptyCommentProblem,
    ConfirmationPermissionDeniedProblem,
    UnconfirmationPermissionDeniedProblem,
    NotConfirmableProblem,
    NotConfirmedProblem,
    AlreadyConfirmedProblem,
    PaymentPermissionDeniedProblem,
    AlreadyPaidProblem,
    NotPayableProblem,
    AccountingPermissionDeniedProblem,
    MismatchedTotalAmountProblem,
    NoAccountingMethodProblem,
)
from fortnox import VoucherRow
from fortnox.api.problems import (
    AlreadyAccountedProblem,
    CashflowVerificationMissingProblem,
    FortnoxRecordMissingProblem,
    FortnoxServiceNotAvailableProblem,
)
from core.permissions import get_permission_provider
from .serializers import (
    InvoiceCreateRequestSerializer,
    InvoiceSerializer,
    InvoicePartSerializer,
    InvoiceAccountSerializer,
)
from ..models import Invoice, InvoicePart
from core.exceptions import (
    UnauthorizedAttestationError,
    UnauthorizedConfirmationError,
    UnauthorizedUnconfirmationError,
    NotConfirmedError,
    DuplicateConfirmationError,
    UnauthorizedAccountingError,
    AlreadyAccountedError,
    FortnoxRecordMissingError,
    CashflowVerificationMissingError,
    MismatchedTotalAmountError,
    NoAccountingMethodError,
)
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_403_FORBIDDEN

logger = get_logger(__name__)


@extend_schema_view(
    list=extend_schema(
        tags=["Invoices"],
        summary="List invoices",
        parameters=list(OPENAPI_PARAMS.values()),
        responses={
            status.HTTP_200_OK: InvoiceSerializer,
            status.HTTP_401_UNAUTHORIZED: problems(NotAuthenticated),
        },
    ),
    create=extend_schema(
        tags=["Invoices"],
        summary="Create an invoice",
        request={"multipart/form-data": InvoiceCreateRequestSerializer},
        responses={
            status.HTTP_201_CREATED: InvoiceSerializer,
            status.HTTP_400_BAD_REQUEST: problems(
                FileRequiredProblem,
                PartInvalidJSONProblem,
                PartRequiredProblem,
                VerificationRequiredError,
            ),
            status.HTTP_422_UNPROCESSABLE_ENTITY: problems(
                InvalidInvoiceDateError, InvalidDueDateError
            ),
        },
    ),
    update=extend_schema(
        tags=["Invoices"],
        summary="Update an invoice",
    ),
    retrieve=extend_schema(
        tags=["Invoices"],
        summary="Retrieve an invoice",
        responses={
            status.HTTP_200_OK: InvoiceSerializer,
            status.HTTP_401_UNAUTHORIZED: problems(NotAuthenticated),
        },
    ),
    partial_update=extend_schema(
        tags=["Invoices"],
        summary="Partially update an invoice",
    ),
    destroy=extend_schema(
        tags=["Invoices"],
        summary="Delete an invoice",
    ),
    comment=extend_schema(
        tags=["Invoices"],
        summary="Comment on an invoice",
        description="Adds a comment to an invoice. The author and date will be set automatically.",
        operation_id="comment_invoice",
        request=CommentCreateSerializer,
        responses={
            status.HTTP_201_CREATED: CommentSerializer,
            status.HTTP_400_BAD_REQUEST: problems(EmptyCommentProblem),
        },
    ),
    confirm=extend_schema(
        tags=["Invoices"],
        summary="Confirm an invoice",
        description="Confirms an invoice. Submit as an empty POST request.",
        operation_id="confirm_invoice",
        request=None,
        responses={
            status.HTTP_204_NO_CONTENT: None,
            status.HTTP_403_FORBIDDEN: problems(ConfirmationPermissionDeniedProblem),
            status.HTTP_409_CONFLICT: problems(
                NotConfirmableProblem, AlreadyConfirmedProblem
            ),
        },
    ),
    unconfirm=extend_schema(
        tags=["Invoices"],
        summary="Unconfirm an invoice",
        description="Removes the confirmation from an invoice. Submit as an empty POST request.",
        operation_id="unconfirm_invoice",
        request=None,
        responses={
            status.HTTP_204_NO_CONTENT: None,
            status.HTTP_403_FORBIDDEN: problems(UnconfirmationPermissionDeniedProblem),
            status.HTTP_409_CONFLICT: problems(NotConfirmedProblem),
        },
    ),
    pay=extend_schema(
        tags=["Invoices"],
        summary="Pay an invoice",
        description="Marks an invoice as paid. Unlike expense reimbursements, invoices are paid one at a time. Submit as an empty POST request. Requires the `pay` permission, and the invoice must be fully attested and not already paid.",
        operation_id="pay_invoice",
        request=None,
        responses={
            status.HTTP_200_OK: InvoiceSerializer,
            status.HTTP_403_FORBIDDEN: problems(PaymentPermissionDeniedProblem),
            status.HTTP_409_CONFLICT: problems(AlreadyPaidProblem, NotPayableProblem),
        },
    ),
    account=extend_schema(
        tags=["Invoices"],
        summary="Account an invoice",
        description=(
            "Records accounting for an invoice. "
            "Pass `voucher_number` to record an existing voucher manually (Fortnox not required). "
            "Pass `voucher_rows` with account/cost-centre/debit/credit data to create a voucher via the Fortnox integration."
        ),
        request=InvoiceAccountSerializer,
        responses={
            status.HTTP_200_OK: InvoiceSerializer,
            status.HTTP_400_BAD_REQUEST: problems(
                PartRequiredProblem,
                NoAccountingMethodProblem,
            ),
            status.HTTP_403_FORBIDDEN: problem(AccountingPermissionDeniedProblem),
            status.HTTP_409_CONFLICT: problems(
                AlreadyAccountedProblem,
                FortnoxRecordMissingProblem,
                CashflowVerificationMissingProblem,
            ),
            status.HTTP_422_UNPROCESSABLE_ENTITY: problem(MismatchedTotalAmountProblem),
            status.HTTP_503_SERVICE_UNAVAILABLE: problem(
                FortnoxServiceNotAvailableProblem
            ),
        },
        operation_id="account_invoice",
    ),
)
class InvoiceViewSet(viewsets.ModelViewSet, AuthenticatedUserMixin):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = [*viewsets.ModelViewSet.http_method_names, "query"]

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
        except (json.JSONDecodeError, TypeError):
            raise PartInvalidJSONProblem(
                detail="There was a problem decoding the parts field. Invoice parts should be submitted as a JSON encoded array."
            )
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        parts_data = cast("list[dict[str, Any]]", data["parts"])
        with transaction.atomic():
            invoice = serializer.save(owner=self.current_user.profile)
            for part in parts_data:
                InvoicePart.objects.create(invoice=invoice, **part)
            for f in files:
                File.objects.create(invoice=invoice, file=normalize_upload(f))

        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        queryset = Invoice.objects.viewable_by(self.current_user)

        if username := self.request.GET.get(Filter.USER):
            try:
                queryset = queryset.filter(
                    owner__user=User.objects.get(username=username)
                )
            except User.DoesNotExist:
                pass

        return (
            apply_invoice_filters(queryset, self.request.GET, self.current_user)
            .distinct()
            .order_by("-created_date")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Recommendations require a GOrdian/Fortnox lookup per part, so only
        # compute them for single-invoice reads (e.g. the accounting page),
        # never for list responses.
        context["include_recommendations"] = self.action == "retrieve"
        return context

    @action(detail=False, methods=["POST", "QUERY"], url_path="search")  # type: ignore[list-item]
    def search(self, request: Request) -> Response:
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
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = Comment.objects.create(
            content=serializer.validated_data["content"],
            invoice=invoice,
            author=self.current_user.profile,
        )
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["POST"])
    def confirm(self, request: Request, pk=None) -> Response:
        with transaction.atomic():
            invoice = Invoice.objects.select_for_update().get(pk=pk)
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
            invoice = Invoice.objects.select_for_update().get(pk=pk)
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
            invoice = Invoice.objects.select_for_update().get(pk=pk)
            if invoice.is_paid():
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
            invoice = Invoice.objects.select_for_update().get(pk=pk)
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


class InvoicePartAttestView(
    generics.GenericAPIView[InvoicePart], AuthenticatedUserMixin
):
    serializer_class = InvoicePartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return InvoicePart.objects.filter(
            invoice__in=Invoice.objects.viewable_by(self.current_user)
        )

    @extend_schema(
        tags=["Invoices"],
        summary="Attest an invoice part",
        description="Attests an invoice part. Submit as an empty POST request.",
        operation_id="attest_invoice_part",
        request=None,
        responses={
            HTTP_204_NO_CONTENT: InvoicePartSerializer,
            HTTP_403_FORBIDDEN: problems(AttestationPermissionDeniedProblem),
        },
    )
    def post(self, request, pk: int):
        invoice_part = self.get_object()

        with transaction.atomic():
            invoice_part = InvoicePart.objects.select_for_update().get(pk=pk)
            try:
                invoice_part.attest(self.current_user)
            except UnauthorizedAttestationError:
                raise AttestationPermissionDeniedProblem(
                    detail=f"You do not have permission to attest this invoice part, {invoice_part.cost_centre} is not a cost centre for which you can attest."
                )

        return Response(
            InvoicePartSerializer(invoice_part).data, status=status.HTTP_204_NO_CONTENT
        )
