"""
API views for expense management.

This module contains all REST API endpoints related to expenses, including
creating, retrieving, updating, and deleting expense records. Each view
handles HTTP request validation, permission checks, and returns JSON responses.

New endpoints should be registered in api/urls.py and follow the existing
patterns for authentication and error handling found in this file.
"""

import json

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from structlog import get_logger

from core.api.filters import apply_expense_filters
from core.api.problems import (
    AccountingPermissionDeniedProblem,
    AlreadyConfirmedProblem,
    ConfirmationPermissionDeniedProblem,
    DeletionPermissionDeniedProblem,
    FileRequiredProblem,
    FlagPermissionDeniedProblem,
    IsFlaggedProblem,
    MismatchedTotalAmountProblem,
    NoAccountingMethodProblem,
    NotConfirmableProblem,
    NotConfirmedProblem,
    PartInvalidJSONProblem,
    PartRequiredProblem,
    UnconfirmationPermissionDeniedProblem,
    UpdatePermissionDeniedProblem,
)
from core.api.serializers import ClaimPartSerializer, CommentSerializer
from core.api.utils import AuthenticatedUserMixin
from core.exceptions import (
    AlreadyAccountedError,
    CashflowVerificationMissingError,
    DuplicateConfirmationError,
    FlaggedConfirmationError,
    FortnoxRecordMissingError,
    MismatchedTotalAmountError,
    NoAccountingMethodError,
    NotConfirmableError,
    NotConfirmedError,
    UnauthorizedAccountingError,
    UnauthorizedConfirmationError,
    UnauthorizedUnconfirmationError,
)
from core.files import normalize_upload
from core.models import Claim, ClaimPart, ClaimQuerySet, Comment, File
from core.permissions import get_permission_provider
from expenses.api.serializers import (
    ExpenseAccountSerializer,
    ExpenseAdminSerializer,
    ExpenseSerializer,
)
from fortnox import VoucherRow
from fortnox.api.problems import (
    AlreadyAccountedProblem,
    CashflowVerificationMissingProblem,
    FortnoxRecordMissingProblem,
    FortnoxServiceNotAvailableProblem,
)
from notifications import get_notification_provider

UserModel = get_user_model()

logger = get_logger(__name__)


class ExpenseViewSet(viewsets.ModelViewSet, AuthenticatedUserMixin):
    # Expenses are addressed by their ExpenseData id, see Claim.data_id
    lookup_field = "expense_data_id"
    lookup_url_kwarg = "pk"
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = [
        *(m for m in viewsets.ModelViewSet.http_method_names if m != "put"),
        "query",
    ]

    def get_serializer_class(self):
        if self.action == "create":
            return ExpenseSerializer
        if self.current_user.profile.may_attest_some():
            return ExpenseAdminSerializer
        return ExpenseSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Recommended accounts require a GOrdian lookup per part, so only
        # compute them for single-expense reads (e.g. the accounting page),
        # never for list responses.
        context["include_recommendations"] = self.action == "retrieve"
        return context

    def create(self, request, *args, **kwargs):

        files = request.FILES.getlist("files")
        if not files:
            raise FileRequiredProblem()

        data = (
            request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
        )
        if isinstance(data.get("parts"), str):
            try:
                data["parts"] = json.loads(data["parts"])
            except json.JSONDecodeError:
                raise PartInvalidJSONProblem()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            expense = serializer.save(owner=self.current_user.profile)
            for f in files:
                File.objects.create(claim=expense, file=normalize_upload(f))

        return Response(ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        expense: Claim = self.get_object()
        assert expense.expense_data is not None
        if expense.expense_data.reimbursement is not None:
            raise DeletionPermissionDeniedProblem()
        if not (
            get_permission_provider().may_delete(self.current_user)
            or expense.owner == self.current_user.profile
        ):
            raise DeletionPermissionDeniedProblem()
        return super().destroy(request, *args, **kwargs)

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        expense: Claim = self.get_object()
        assert expense.expense_data is not None
        if expense.expense_data.reimbursement_id is not None:
            raise UpdatePermissionDeniedProblem()
        if not expense.owner == self.current_user.profile:
            raise UpdatePermissionDeniedProblem()

        data = (
            request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
        )

        # Allow passing IDs for files to be removed
        if deletes := data.pop("delete_files", None):
            try:
                deletes_data: list[int] = json.loads(deletes)
                expense.file_set.filter(id__in=deletes_data).delete()
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

        serializer = self.get_serializer(expense, data=data, partial=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            serializer.save()
            if parts_data is not None:
                expense.parts.all().delete()
                for part in parts_data:
                    ClaimPart.objects.create(claim=expense, **part)
            if parts_data is not None or deletes:
                expense.reset_confirmation()
            for f in files:
                File.objects.create(claim=expense, file=normalize_upload(f))

            expense.expense_data.is_flagged = False
            expense.expense_data.save(update_fields=["is_flagged"])

        expense.refresh_from_db()
        return Response(
            ExpenseSerializer(expense, context=self.get_serializer_context()).data
        )

    def get_queryset(self) -> ClaimQuerySet:
        queryset = (
            Claim.objects.expenses()
            .select_related(
                "owner__user",
                "expense_data__confirmed_by__profile__user",
                "expense_data__reimbursement__payer__user",
                "expense_data__reimbursement__receiver__user",
            )
            .prefetch_related(
                "file_set",
                "parts__attested_by__user",
                "comment_set__author__user",
            )
            .viewable_by(self.current_user)
            .with_total()
        )
        return apply_expense_filters(
            queryset, self.request.GET, self.current_user
        ).distinct()

    @action(detail=False, methods=["POST", "QUERY"], url_path="search")  # type: ignore[list-item]
    def search(self, request: Request) -> Response:
        assert isinstance(request.data, dict)
        query = request.data.get("query") or {}
        expenses = self.get_queryset().search(**query)
        page = self.paginate_queryset(expenses)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(ExpenseSerializer(expenses, many=True).data)

    @action(detail=True, methods=["POST"], url_path="comments")
    def comment(self, request: Request, pk=None) -> Response:
        expense = self.get_object()

        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = Comment.objects.create(
            claim=expense,
            content=serializer.validated_data["content"],
            author=self.current_user.profile,
        )

        get_notification_provider().on_comment(expense, comment)

        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["POST"])
    def confirm(self, request: Request, pk=None) -> Response:
        with transaction.atomic():
            expense = Claim.objects.select_for_update().get(expense_data_id=pk)
            try:
                expense.confirm(self.current_user)
            except UnauthorizedConfirmationError as e:
                raise ConfirmationPermissionDeniedProblem(
                    detail="You are not authorized to confirm this expense."
                ) from e
            except FlaggedConfirmationError as e:
                raise IsFlaggedProblem(
                    detail="This expense is flagged and cannot be confirmed."
                ) from e
            except NotConfirmableError as e:
                raise NotConfirmableProblem() from e
            except DuplicateConfirmationError as e:
                raise AlreadyConfirmedProblem(
                    detail="This expense has already been confirmed."
                ) from e
            expense.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["POST"])
    def unconfirm(self, request: Request, pk=None) -> Response:
        with transaction.atomic():
            expense = Claim.objects.select_for_update().get(expense_data_id=pk)
            try:
                expense.unconfirm(self.current_user)
            except UnauthorizedUnconfirmationError as e:
                raise UnconfirmationPermissionDeniedProblem() from e
            except NotConfirmedError as e:
                raise NotConfirmedProblem() from e
            expense.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["POST"])
    def flag(self, request: Request, pk=None) -> Response:
        if not self.current_user.profile.may_flag():
            raise FlagPermissionDeniedProblem()
        expense = self.get_object()
        expense.expense_data.is_flagged = True
        expense.expense_data.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["POST"])
    def unflag(self, request: Request, pk=None) -> Response:
        if not self.current_user.profile.may_flag():
            raise FlagPermissionDeniedProblem()
        expense: Claim = self.get_object()
        assert expense.expense_data is not None
        expense.expense_data.is_flagged = False
        expense.expense_data.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["POST"])
    def account(self, request: Request, pk=None) -> Response:
        serializer = ExpenseAccountSerializer(data=request.data)
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
            expense = Claim.objects.select_for_update().get(expense_data_id=pk)
            try:
                expense.account(
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
        return Response(ExpenseSerializer(expense).data, status=status.HTTP_200_OK)
