from typing import ClassVar

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from core.api.problems import PartRequiredProblem
from core.api.serializers import (
    ClaimPartSerializer,
    ClaimTotalField,
    CommentSerializer,
    FileSerializer,
    ProfileSerializer,
    VoucherRowSerializer,
)
from core.models import Claim
from invoices.models import InvoiceData

from .problems import (
    InvalidInvoiceDateError,
    VerificationRequiredError,
)


class InvoiceAccountSerializer(serializers.Serializer):
    voucher_number = serializers.RegexField(r"[A-Z]\d+", required=False)
    voucher_description = serializers.CharField(allow_blank=False, required=False)
    voucher_rows = VoucherRowSerializer(many=True, required=False)


class InvoiceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="data_id", read_only=True)
    files = FileSerializer(many=True, source="file_set", read_only=True)
    owner = ProfileSerializer(read_only=True)
    parts = ClaimPartSerializer(many=True, read_only=True)

    invoice_date = serializers.DateField(
        source="invoice_data.invoice_date", allow_null=True
    )
    due_date = serializers.DateField(source="invoice_data.due_date", allow_null=True)
    invoice_number = serializers.CharField(source="invoice_data.invoice_number")

    paid_by = ProfileSerializer(
        source="invoice_data.paid_by", allow_null=True, read_only=True
    )
    paid_at = serializers.DateField(
        source="invoice_data.paid_at", allow_null=True, read_only=True
    )

    # Note that DRF serializers strip whitespace by default
    verification = serializers.RegexField(r"[A-Z]\d+", required=False)
    voucher = serializers.SerializerMethodField(
        help_text="Fortnox voucher (verification) number. Null if not yet accounted."
    )

    comments = CommentSerializer(many=True, read_only=True, source="comment_set")
    total = ClaimTotalField()

    recommended_credit_account = serializers.SerializerMethodField(
        help_text=(
            "Fortnox account to credit when creating a voucher for this "
            "invoice (the accounts payable account). Null in list responses."
        )
    )

    class Meta:
        model = Claim
        fields: ClassVar = [
            "id",
            "created_date",
            "invoice_date",
            "invoice_number",
            "due_date",
            "owner",
            "description",
            "verification",
            "voucher",
            "parts",
            "comments",
            "files",
            "paid_by",
            "paid_at",
            "recommended_credit_account",
            "total",
        ]

    def get_voucher(self, invoice: Claim) -> str | None:
        # Model stores "" for not-yet-accounted; API exposes null
        return invoice.verification or None

    def get_recommended_credit_account(self, invoice: Claim) -> int | None:
        if not self.context.get("include_recommendations"):
            return None
        return settings.FORTNOX_INVOICE_CREDIT_ACCOUNT

    def validate(self, attrs):

        invoice_date = attrs.get("invoice_data", {}).get("invoice_date")
        if invoice_date and invoice_date > timezone.localdate():
            raise InvalidInvoiceDateError()

        parts = attrs.get("parts")
        if parts and len(parts) <= 0:
            raise PartRequiredProblem()

        accounted = self.initial_data.get("accounted") in (True, "True", "true", "1")
        verification = attrs.get("verification")
        if accounted and not verification:
            raise VerificationRequiredError()

        return attrs

    def create(self, validated_data):
        # Parts are created by the view, see InvoiceViewSet.create
        invoice_data = InvoiceData.objects.create(**validated_data.pop("invoice_data"))
        return Claim.objects.create(invoice_data=invoice_data, **validated_data)

    def update(self, instance, validated_data):
        if invoice_data := validated_data.pop("invoice_data", None):
            for attr, value in invoice_data.items():
                setattr(instance.invoice_data, attr, value)
            instance.invoice_data.save()
        return super().update(instance, validated_data)
