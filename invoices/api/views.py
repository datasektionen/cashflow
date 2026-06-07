import json
from typing import cast

from django.contrib.auth.models import User
from django.db import transaction
from django.http import QueryDict
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework import generics, viewsets, status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from structlog import get_logger

from core.api.filters import Filter
from core.api.openapi import problems
from core.api.utils import AuthenticatedUserMixin
from expenses.models import File
from .exceptions import (
    InvalidInvoiceDateError,
    InvalidDueDateError,
    VerificationRequiredError,
)
from core.api.exceptions import (
    PartInvalidJSONError,
    FileRequiredError,
    PartRequiredError,
    AttestationPermissionDenied,
)
from .serializers import (
    InvoiceCreateRequestSerializer,
    InvoiceSerializer,
    InvoicePartSerializer,
)
from ..models import Invoice, InvoicePart
from core.exceptions import UnauthorizedAttestationError
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_403_FORBIDDEN

logger = get_logger(__name__)


@extend_schema_view(
    list=extend_schema(
        tags=["Invoices"],
        summary="List invoices",
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
                FileRequiredError,
                PartInvalidJSONError,
                PartRequiredError,
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
)
class InvoiceViewSet(viewsets.ModelViewSet, AuthenticatedUserMixin):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request: Request, *args, **kwargs) -> Response:

        files = request.FILES.getlist("files")
        if not files:
            raise FileRequiredError()
        data = cast(QueryDict, request.data).dict()
        try:
            parts_raw = cast("str | None", data.get("parts"))
            if parts_raw is None:
                raise PartRequiredError()
            data["parts"] = json.loads(parts_raw)
        except json.JSONDecodeError, TypeError:
            raise PartInvalidJSONError(
                detail="There was a problem decoding the parts field. Invoice parts should be submitted as a JSON encoded array."
            )
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            invoice = serializer.save(owner=self.current_user.profile)
            for f in files:
                File.objects.create(invoice=invoice, file=f)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        filter_map = {}
        if self.request.GET.get(Filter.USER):
            try:
                filtered_user = User.objects.get(
                    username=self.request.GET.get(Filter.USER)
                )
                filter_map["owner__user"] = filtered_user
            except User.DoesNotExist:
                pass
        if self.request.GET.get(Filter.COST_CENTER):
            filter_map["invoicepart__cost_centre__in"] = [
                self.request.GET.get(Filter.COST_CENTER),
            ]

        return (
            Invoice.objects.viewable_by(self.current_user)
            .filter(**filter_map)
            .distinct()
            .order_by("-invoice_date")
        )


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
            HTTP_403_FORBIDDEN: problems(AttestationPermissionDenied),
        },
    )
    def post(self, request, pk: int):
        invoice_part = self.get_object()

        with transaction.atomic():
            invoice_part = InvoicePart.objects.select_for_update().get(pk=pk)
            try:
                invoice_part.attest(self.current_user)
            except UnauthorizedAttestationError:
                raise AttestationPermissionDenied(
                    detail=f"You do not have permission to attest this invoice part, {invoice_part.cost_centre} is not a cost centre for which you can attest."
                )

        return Response(
            InvoicePartSerializer(invoice_part).data, status=status.HTTP_204_NO_CONTENT
        )
