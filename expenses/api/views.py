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
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_400_BAD_REQUEST,
    HTTP_201_CREATED,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_403_FORBIDDEN,
    HTTP_204_NO_CONTENT,
)
from structlog import get_logger

from core.api.problems import (
    AccountingPermissionDeniedProblem,
    AlreadyConfirmedProblem,
    AttestationPermissionDeniedProblem,
    ConfirmationPermissionDeniedProblem,
    UnconfirmationPermissionDeniedProblem,
    NotConfirmedProblem,
    EmptyCommentProblem,
    FileRequiredProblem,
    FlagPermissionDeniedProblem,
    IsFlaggedProblem,
    NotConfirmableProblem,
    PartInvalidJSONProblem,
    PartRequiredProblem,
)
from core.api.filters import Filter, apply_expense_filters, OPENAPI_PARAMS
from core.api.openapi import problem, problems
from core.api.serializers import CommentSerializer, CommentCreateSerializer
from core.api.utils import AuthenticatedUserMixin
from core.exceptions import (
    UnauthorizedAttestationError,
    SelfAttestationError,
    FlaggedAttestationError,
    UnauthorizedConfirmationError,
    UnauthorizedUnconfirmationError,
    NotConfirmedError,
    NotConfirmableError,
    FlaggedConfirmationError,
    DuplicateConfirmationError,
    UnauthorizedAccountingError,
    AlreadyAccountedError,
    FortnoxRecordMissingError,
    CashflowVerificationMissingError,
)
from expenses.api.problems import InvalidExpenseDateError
from expenses.api.serializers import (
    ExpenseAccountSerializer,
    ExpensePartSerializer,
    ExpenseSerializer,
    ExpenseAdminSerializer,
    ExpenseCreateSerializer,
)
from expenses.models import Expense, ExpensePart, File, Comment
from fortnox.api.problems import (
    AlreadyAccountedProblem,
    CashflowVerificationMissingProblem,
    FortnoxRecordMissingProblem,
    FortnoxServiceNotAvailableProblem,
)

UserModel = get_user_model()

logger = get_logger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="List expenses",
        operation_id="list_expenses",
        tags=["Expenses"],
        parameters=list(OPENAPI_PARAMS.values()),
        responses={
            HTTP_200_OK: ExpenseAdminSerializer,
            HTTP_401_UNAUTHORIZED: problem(NotAuthenticated),
        },
    ),
    retrieve=extend_schema(
        summary="Retrieve an expense",
        description=(
            "Returns a single expense by ID, including its parts, owner "
            "profile, and attached files."
        ),
        operation_id="retrieve_expense",
        tags=["Expenses"],
    ),
    create=extend_schema(
        summary="Create a new expense",
        request={"multipart/form-data": ExpenseCreateSerializer},
        description=(
            "Creates an expense together with its parts and one or more "
            "attached receipt files. Submit as `multipart/form-data` with "
            "the `parts` field as a JSON-encoded array; at least one file "
            "is required."
        ),
        responses={
            HTTP_201_CREATED: ExpenseSerializer,
            HTTP_400_BAD_REQUEST: problems(
                FileRequiredProblem, PartRequiredProblem, PartInvalidJSONProblem
            ),
            HTTP_401_UNAUTHORIZED: problem(NotAuthenticated),
            HTTP_422_UNPROCESSABLE_ENTITY: problem(InvalidExpenseDateError),
        },
        operation_id="create_expense",
        tags=["Expenses"],
    ),
    update=extend_schema(
        summary="Update an expense",
        description=(
            "Replaces an expense in full. All writable fields must be " "provided."
        ),
        operation_id="update_expense",
        tags=["Expenses"],
    ),
    partial_update=extend_schema(
        summary="Partially update an expense",
        description=(
            "Updates a subset of fields on an existing expense. Only the "
            "fields included in the request body are changed."
        ),
        operation_id="partial_update_expense",
        tags=["Expenses"],
    ),
    destroy=extend_schema(
        summary="Delete an expense",
        description="Permanently deletes an expense and its associated parts.",
        operation_id="delete_expense",
        tags=["Expenses"],
    ),
    comment=extend_schema(
        tags=["Expenses"],
        summary="Comment on an expense",
        description="Adds a comment to an expense. The author and date will be set automatically.",
        request=CommentCreateSerializer,
        responses={
            status.HTTP_201_CREATED: CommentSerializer,
            status.HTTP_400_BAD_REQUEST: problems(EmptyCommentProblem),
        },
        operation_id="add_expense_comment",
    ),
    confirm=extend_schema(
        tags=["Expenses"],
        summary="Confirm an expense",
        description="Marks an expense as confirmed. Submit as an empty POST request.",
        request=None,
        responses={
            status.HTTP_204_NO_CONTENT: None,
            status.HTTP_403_FORBIDDEN: problem(ConfirmationPermissionDeniedProblem),
            status.HTTP_409_CONFLICT: problems(
                AlreadyConfirmedProblem, IsFlaggedProblem, NotConfirmableProblem
            ),
        },
        operation_id="confirm_expense",
    ),
    unconfirm=extend_schema(
        tags=["Expenses"],
        summary="Unconfirm an expense",
        description="Removes the confirmation from an expense. Submit as an empty POST request.",
        request=None,
        responses={
            status.HTTP_204_NO_CONTENT: None,
            status.HTTP_403_FORBIDDEN: problem(UnconfirmationPermissionDeniedProblem),
            status.HTTP_409_CONFLICT: problem(NotConfirmedProblem),
        },
        operation_id="unconfirm_expense",
    ),
    flag=extend_schema(
        tags=["Expenses"],
        summary="Flag an expense",
        description="Marks an expense as flagged. Submit as an empty POST request.",
        request=None,
        responses={
            status.HTTP_204_NO_CONTENT: None,
            status.HTTP_403_FORBIDDEN: problem(FlagPermissionDeniedProblem),
        },
        operation_id="flag_expense",
    ),
    unflag=extend_schema(
        tags=["Expenses"],
        summary="Unflag an expense",
        description="Removes the flag from an expense. Submit as an empty POST request.",
        request=None,
        responses={
            status.HTTP_204_NO_CONTENT: None,
            status.HTTP_403_FORBIDDEN: problem(FlagPermissionDeniedProblem),
        },
        operation_id="unflag_expense",
    ),
    account=extend_schema(
        tags=["Expenses"],
        summary="Account an expense",
        description=(
            "Records accounting for an expense. "
            "Pass `voucher_number` to record an existing voucher manually (Fortnox not required). "
            "Pass `parts` with account/cost-centre data to create a voucher via the Fortnox integration."
        ),
        request=ExpenseAccountSerializer,
        responses={
            status.HTTP_200_OK: ExpenseSerializer,
            status.HTTP_400_BAD_REQUEST: problem(PartRequiredProblem),
            status.HTTP_403_FORBIDDEN: problem(AccountingPermissionDeniedProblem),
            status.HTTP_409_CONFLICT: problems(
                AlreadyAccountedProblem,
                FortnoxRecordMissingProblem,
                CashflowVerificationMissingProblem,
            ),
            status.HTTP_503_SERVICE_UNAVAILABLE: problem(
                FortnoxServiceNotAvailableProblem
            ),
        },
        operation_id="account_expense",
    ),
)
class ExpenseViewSet(viewsets.ModelViewSet, AuthenticatedUserMixin):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return ExpenseSerializer
        if self.current_user.profile.may_attest_some():
            return ExpenseAdminSerializer
        return ExpenseSerializer

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
                File.objects.create(expense=expense, file=f)

        return Response(ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        queryset = Expense.objects.viewable_by(self.current_user)

        if username := self.request.GET.get(Filter.USER):
            try:
                queryset = queryset.filter(
                    owner__user=UserModel.objects.get(username=username)
                )
            except UserModel.DoesNotExist:
                pass

        return (
            apply_expense_filters(queryset, self.request.GET, self.current_user)
            .distinct()
            .order_by("-created_date")
        )

    @action(detail=True, methods=["POST"], url_path="comments")
    def comment(self, request: Request, pk=None) -> Response:
        expense = self.get_object()

        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = Comment.objects.create(
            expense=expense,
            content=serializer.validated_data["content"],
            author=self.current_user.profile,
        )
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["POST"])
    def confirm(self, request: Request, pk=None) -> Response:
        with transaction.atomic():
            expense = Expense.objects.select_for_update().get(pk=pk)
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
            expense = Expense.objects.select_for_update().get(pk=pk)
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
        expense.is_flagged = True
        expense.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["POST"])
    def unflag(self, request: Request, pk=None) -> Response:
        if not self.current_user.profile.may_flag():
            raise FlagPermissionDeniedProblem()
        expense = self.get_object()
        expense.is_flagged = False
        expense.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["POST"])
    def account(self, request: Request, pk=None) -> Response:
        serializer = ExpenseAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        voucher_number = serializer.validated_data.get("voucher_number")
        parts_data = serializer.validated_data.get("parts", [])
        part_accounts = {
            p["part_id"]: (p["account_number"], p["cost_centre"]) for p in parts_data
        } or None

        fortnox_client = None
        if not voucher_number:
            fortnox_client = getattr(request, "fortnox_service", None)
            if fortnox_client is None:
                raise FortnoxServiceNotAvailableProblem()
            if not part_accounts:
                raise PartRequiredProblem()

        with transaction.atomic():
            expense = Expense.objects.select_for_update().get(pk=pk)
            try:
                expense.account(
                    self.current_user,
                    fortnox_client=fortnox_client,
                    part_accounts=part_accounts,
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
        return Response(ExpenseSerializer(expense).data, status=status.HTTP_200_OK)


class ExpensePartAttestView(
    generics.GenericAPIView[ExpensePart], AuthenticatedUserMixin
):
    serializer_class = ExpensePartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ExpensePart.objects.filter(
            expense__in=Expense.objects.viewable_by(self.current_user)
        )

    @extend_schema(
        tags=["Expenses"],
        summary="Attest an expense part",
        description="Attests an expense part. Submit as an empty POST request.",
        operation_id="attest",
        request=None,
        responses={
            HTTP_204_NO_CONTENT: None,
            HTTP_403_FORBIDDEN: problems(AttestationPermissionDeniedProblem),
        },
    )
    def post(self, request, pk: int):
        expense_part = self.get_object()

        with transaction.atomic():
            expense_part = ExpensePart.objects.select_for_update().get(pk=pk)
            try:
                expense_part.attest(self.current_user)
            except FlaggedAttestationError:
                raise IsFlaggedProblem(
                    detail="This expense is flagged and cannot be attested."
                )
            except UnauthorizedAttestationError:
                raise AttestationPermissionDeniedProblem(
                    detail=f"You do not have permission to attest this expense part, {expense_part.cost_centre} is not a cost centre for which you can attest."
                )
            except SelfAttestationError:
                raise AttestationPermissionDeniedProblem(
                    detail="You do not have permission to attest this expense part, you cannot attest for your own expenses."
                )

        return Response(status=status.HTTP_204_NO_CONTENT)
