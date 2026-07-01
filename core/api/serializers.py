from datetime import date
from typing import TypedDict

from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.fields import CharField
from rest_framework.relations import PrimaryKeyRelatedField

from core.api.problems import EmptyCommentProblem, NoExpensesProblem
from expenses.models import File, Profile, Comment, Payment, ExpensePart, Expense
from invoices.models import InvoicePart


class ClaimData(TypedDict):
    id: int
    type: str
    description: str
    amount: str
    created_date: date
    is_attested: bool
    is_confirmed: bool
    is_paid: bool
    owner: Profile
    parts: QuerySet[InvoicePart | ExpensePart]


class ProblemDetailSerializer(serializers.Serializer):
    type = serializers.URLField()
    title = serializers.CharField()
    detail = serializers.CharField()
    status = serializers.IntegerField()
    code = serializers.CharField()


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = "__all__"


class ProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name", allow_blank=False)
    last_name = serializers.CharField(source="user.last_name", allow_blank=False)
    email = serializers.EmailField(source="user.email", allow_blank=False)
    username = serializers.CharField(source="user.username", allow_blank=False)

    class Meta:
        model = Profile
        fields = ["id", "first_name", "last_name", "email", "username"]


class ClaimPartSerializer(serializers.Serializer):
    cost_centre = serializers.CharField()
    secondary_cost_centre = serializers.CharField()
    budget_line = serializers.CharField()
    amount = serializers.CharField()
    attested_by = ProfileSerializer(read_only=True)
    attest_date = serializers.DateField(allow_null=True)


class ClaimSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    description = serializers.CharField()
    amount = serializers.CharField()
    created_date = serializers.DateField()
    is_attested = serializers.BooleanField(read_only=True)
    is_confirmed = serializers.BooleanField(read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    owner = ProfileSerializer(read_only=True)
    parts = ClaimPartSerializer(many=True)


class PaymentSerializer(serializers.ModelSerializer):
    payer = ProfileSerializer(read_only=True)
    receiver = ProfileSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "date", "payer", "receiver"]


class CommentSerializer(serializers.ModelSerializer):
    author = ProfileSerializer(read_only=True)
    date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Comment
        fields = ["date", "author", "content"]


class CommentCreateSerializer(serializers.Serializer):
    content = serializers.CharField(
        allow_blank=True, help_text="The body of the comment, must be non-empty."
    )

    def validate_content(self, value):
        if not value.strip():
            raise EmptyCommentProblem()
        return value


@extend_schema_field(OpenApiTypes.BINARY)
class UploadField(serializers.FileField):
    pass


class AccountSerializer(serializers.Serializer):
    part_id = serializers.IntegerField()
    cost_centre = serializers.CharField(allow_blank=False)
    account_number = serializers.IntegerField(min_value=0, max_value=9999)


class VoucherRowSerializer(serializers.Serializer):
    account = serializers.IntegerField(min_value=0, max_value=9999, required=True)
    cost_centre = serializers.IntegerField(min_value=0, max_value=9999, required=True)
    debit = serializers.DecimalField(
        decimal_places=2, max_digits=9, min_value=0, required=False
    )
    credit = serializers.DecimalField(
        decimal_places=2, max_digits=9, min_value=0, required=False
    )


class PendingPaymentsSerializer(serializers.Serializer):
    # Include all normal Profile fields
    owner = ProfileSerializer(source="*", read_only=True)
    total = serializers.DecimalField(max_digits=11, decimal_places=2, read_only=True)
    count = serializers.IntegerField(read_only=True)


class PaymentCreateSerializer(serializers.Serializer):
    """Request body for creating a payment: the expenses to reimburse in one go."""

    expenses = PrimaryKeyRelatedField(
        many=True,
        allow_empty=True,
        queryset=Expense.objects.all(),
        help_text="IDs of the expenses to reimburse. All must belong to the same user.",
    )

    def validate_expenses(self, value):
        if not value:
            raise NoExpensesProblem()
        return value
