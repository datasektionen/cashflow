from rest_framework import serializers
from rest_framework.fields import DateField
from rest_framework.relations import PrimaryKeyRelatedField

from core.api.serializers import (
    FileSerializer,
    ProfileSerializer,
    UploadField,
    CommentSerializer,
    PaymentSerializer,
    VoucherRowSerializer,
)
from expenses.models import Expense, ExpensePart, Payment


class ExpensePartSerializer(serializers.ModelSerializer):
    expense: PrimaryKeyRelatedField[Expense] = PrimaryKeyRelatedField(read_only=True)
    attested_by = ProfileSerializer(read_only=True)
    attest_date = DateField(read_only=True)

    class Meta:
        model = ExpensePart
        fields = [
            "id",
            "expense",
            "cost_centre",
            "secondary_cost_centre",
            "budget_line",
            "amount",
            "attested_by",
            "attest_date",
        ]


class ExpenseSerializer(serializers.ModelSerializer):
    files = FileSerializer(many=True, source="file_set", read_only=True)
    owner = ProfileSerializer(read_only=True)
    parts = ExpensePartSerializer(many=True, required=True, allow_empty=False)
    confirmed_by = ProfileSerializer(read_only=True, source="confirmed_by.profile")
    comments = CommentSerializer(many=True, read_only=True, source="comment_set")
    payment = PaymentSerializer(read_only=True, source="payment_set")
    # Note that DRF serializers strip whitespace by default
    verification = serializers.RegexField(r"[A-Z]\d+", required=False)

    class Meta:
        model = Expense
        fields = [
            "id",
            "created_date",
            "expense_date",
            "confirmed_by",
            "confirmed_at",
            "owner",
            "description",
            "reimbursement",
            "verification",
            "files",
            "parts",
            "comments",
            "payment",
        ]

    def create(self, validated_data):
        parts_data = validated_data.pop("parts", [])
        expense = Expense.objects.create(**validated_data)
        for part in parts_data:
            ExpensePart.objects.create(expense=expense, **part)
        return expense


class ExpenseAdminSerializer(ExpenseSerializer):
    """Dedicated serializers for creating claims, provides proper annotations for OpenAPI."""

    is_flagged = serializers.BooleanField(
        help_text="Whether the expense is flagged. Only included for users with attesting permissions.",
    )

    class Meta(ExpenseSerializer.Meta):
        fields = [*ExpenseSerializer.Meta.fields, "is_flagged"]


class ExpenseCreateSerializer(serializers.ModelSerializer):
    """Dedicated serializer for creating claims, provides proper annotations for OpenAPI."""

    files = serializers.ListField(child=UploadField())
    parts = serializers.CharField(
        help_text="JSON-encoded array of expense parts: [{cost_centre, secondary_cost_centre, budget_line, amount}]."
    )

    class Meta:
        model = Expense
        fields = ["expense_date", "description", "files", "parts"]


class ExpenseAccountSerializer(serializers.Serializer):
    voucher_number = serializers.RegexField(r"[A-Z]\d+", required=False)
    voucher_rows = VoucherRowSerializer(many=True, required=False)


class ExpensePaymentSerializer(serializers.ModelSerializer):
    payer = ProfileSerializer(read_only=True, source="payer.profile")
    receiver = ProfileSerializer(read_only=True, source="receiver.profile")
    expenses = PrimaryKeyRelatedField(
        queryset=Expense.objects.all(), many=True, source="expense_set"
    )

    class Meta:
        model = Payment
        fields = ["id", "date", "payer", "receiver", "expenses"]
