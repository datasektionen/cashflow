from typing import ClassVar

from django.conf import settings
from rest_framework import serializers

from core.api.serializers import (
    ClaimPartSerializer,
    CommentSerializer,
    FileSerializer,
    ProfileSerializer,
    VoucherRowSerializer,
)
from core.models import Claim, ClaimPart
from expenses.models import ExpenseData, Payment


class PaymentSerializer(serializers.ModelSerializer):
    payer = ProfileSerializer(read_only=True)
    receiver = ProfileSerializer(read_only=True)
    tag = serializers.CharField(
        read_only=True,
        help_text="Bank-facing payment reference, e.g. 'Data1234'.",
    )
    total = serializers.DecimalField(
        max_digits=11, decimal_places=2, source="amount", read_only=True
    )

    class Meta:
        model = Payment
        fields: ClassVar = ["id", "date", "payer", "receiver", "tag", "total"]


class ExpenseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="data_id", read_only=True)
    files = FileSerializer(many=True, source="file_set", read_only=True)
    owner = ProfileSerializer(read_only=True)
    parts = ClaimPartSerializer(many=True, required=True, allow_empty=False)
    expense_date = serializers.DateField(source="expense_data.expense_date")
    confirmed_by = ProfileSerializer(
        read_only=True, source="expense_data.confirmed_by.profile", allow_null=True
    )
    confirmed_at = serializers.DateField(
        read_only=True, source="expense_data.confirmed_at", allow_null=True
    )
    comments = CommentSerializer(many=True, read_only=True, source="comment_set")
    reimbursement = serializers.IntegerField(
        read_only=True, source="expense_data.reimbursement_id", allow_null=True
    )
    payment = PaymentSerializer(
        read_only=True, source="expense_data.reimbursement", allow_null=True
    )
    # Note that DRF serializers strip whitespace by default
    verification = serializers.RegexField(r"[A-Z]\d+", required=False)
    voucher = serializers.SerializerMethodField(
        help_text="Fortnox voucher (verification) number. Null if not yet accounted."
    )
    recommended_credit_account = serializers.SerializerMethodField(
        help_text=(
            "Fortnox account to credit when creating a voucher for this "
            "expense (the reimbursement liability account). Null in list "
            "responses."
        )
    )

    class Meta:
        model = Claim
        fields: ClassVar = [
            "id",
            "created_date",
            "expense_date",
            "confirmed_by",
            "confirmed_at",
            "owner",
            "description",
            "reimbursement",
            "verification",
            "voucher",
            "files",
            "parts",
            "comments",
            "payment",
            "recommended_credit_account",
        ]

    def get_voucher(self, expense: Claim) -> str | None:
        # Model stores "" for not-yet-accounted; API exposes null
        return expense.verification or None

    def get_recommended_credit_account(self, expense: Claim) -> int | None:
        if not self.context.get("include_recommendations"):
            return None
        return settings.FORTNOX_EXPENSE_CREDIT_ACCOUNT

    def create(self, validated_data):
        parts_data = validated_data.pop("parts", [])
        expense_data = ExpenseData.objects.create(**validated_data.pop("expense_data"))
        expense = Claim.objects.create(expense_data=expense_data, **validated_data)
        for part in parts_data:
            ClaimPart.objects.create(claim=expense, **part)
        return expense

    def update(self, instance, validated_data):
        # Parts are replaced by the view, see ExpenseViewSet.partial_update
        validated_data.pop("parts", None)
        if expense_data := validated_data.pop("expense_data", None):
            for attr, value in expense_data.items():
                setattr(instance.expense_data, attr, value)
            instance.expense_data.save()
        return super().update(instance, validated_data)


class ExpenseAdminSerializer(ExpenseSerializer):
    is_flagged = serializers.BooleanField(
        help_text="Whether the expense is flagged. Only included for users with attesting permissions.",
        source="expense_data.is_flagged",
        allow_null=True,
    )

    class Meta(ExpenseSerializer.Meta):
        fields: ClassVar = [*ExpenseSerializer.Meta.fields, "is_flagged"]


class ExpenseAccountSerializer(serializers.Serializer):
    voucher_number = serializers.RegexField(r"[A-Z]\d+", required=False)
    voucher_rows = VoucherRowSerializer(many=True, required=False)
