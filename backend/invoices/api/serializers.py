import datetime

from django.conf import settings
from rest_framework import serializers

from cashflow.api.serializers import PartRecommendationsMixin
from core.api.serializers import (
    ProfileSerializer,
    UploadField,
    CommentSerializer,
    PaymentSerializer,
    FileSerializer,
    VoucherRowSerializer,
)
from invoices.models import Invoice, InvoicePart
from .problems import (
    InvalidInvoiceDateError,
    InvalidDueDateError,
    VerificationRequiredError,
)
from core.api.problems import InvalidDateFormatProblem, PartRequiredProblem


class InvoiceDateField(serializers.DateField):
    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", ["%Y-%m-%d"])
        super().__init__(**kwargs)

    def to_internal_value(self, value):
        try:
            return super().to_internal_value(value)
        except serializers.ValidationError:
            raise InvalidDateFormatProblem()


class InvoiceCreateRequestSerializer(serializers.Serializer):
    """Schema-only serializer describing the multipart/form-data payload for invoice creation."""

    files = serializers.ListField(
        child=UploadField(),
        help_text="One or more images or PDFs of the invoice.",
    )
    description = serializers.CharField()
    invoice_date = serializers.DateField(
        help_text="Date the invoice was issued (YYYY-MM-DD)."
    )
    due_date = serializers.DateField(help_text="Payment due date (YYYY-MM-DD).")
    parts = serializers.CharField(
        help_text="JSON-encoded array of invoice parts: [{cost_centre, secondary_cost_centre, budget_line, amount}]."
    )
    accounted = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Whether the invoice has already been booked.",
    )
    verification = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Verification number, required when accounted=true.",
    )


class InvoiceAccountSerializer(serializers.Serializer):
    voucher_number = serializers.RegexField(r"[A-Z]\d+", required=False)
    voucher_rows = VoucherRowSerializer(many=True, required=False)


class InvoicePartSerializer(PartRecommendationsMixin, serializers.ModelSerializer):
    attested_by = ProfileSerializer(read_only=True)

    class Meta:
        model = InvoicePart
        fields = [
            "id",
            "invoice",
            "cost_centre",
            "secondary_cost_centre",
            "budget_line",
            "amount",
            "attested_by",
            "attest_date",
            "recommended_accounts",
            "recommended_cost_centre",
        ]


class InvoiceSerializer(serializers.ModelSerializer):

    files = FileSerializer(many=True, source="file_set", read_only=True)
    owner = ProfileSerializer(read_only=True)
    confirmed_by = ProfileSerializer(
        source="confirmed_by.profile", allow_null=True, read_only=True
    )
    parts = InvoicePartSerializer(many=True, read_only=True)
    invoice_date = InvoiceDateField(allow_null=True)
    due_date = InvoiceDateField(allow_null=True)

    # There is a typo in the Invoice model
    # https://github.com/datasektionen/cashflow/issues/311#issue-4554872870
    paid_by = ProfileSerializer(
        source="payed_by.profile", allow_null=True, read_only=True
    )
    paid_at = serializers.DateField(source="payed_at", allow_null=True, read_only=True)

    # Note that DRF serializers strip whitespace by default
    verification = serializers.RegexField(r"[A-Z]\d+", required=False)

    comments = CommentSerializer(many=True, read_only=True, source="comment_set")

    recommended_credit_account = serializers.SerializerMethodField(
        help_text=(
            "Fortnox account to credit when creating a voucher for this "
            "invoice (the accounts payable account). Null in list responses."
        )
    )

    class Meta:
        model = Invoice
        fields = [
            "id",
            "created_date",
            "invoice_date",
            "due_date",
            "confirmed_by",
            "confirmed_at",
            "owner",
            "description",
            "verification",
            "parts",
            "comments",
            "files",
            "paid_by",
            "paid_at",
            "recommended_credit_account",
        ]

    def get_recommended_credit_account(self, invoice: Invoice) -> int | None:
        if not self.context.get("include_recommendations"):
            return None
        return settings.FORTNOX_INVOICE_CREDIT_ACCOUNT

    def validate(self, data):

        invoice_date = data.get("invoice_date")
        if invoice_date and invoice_date > datetime.date.today():
            raise InvalidInvoiceDateError()

        due_date = data.get("due_date")
        if due_date and due_date < datetime.date.today():
            raise InvalidDueDateError()

        parts = data.get("parts")
        if parts and len(parts) <= 0:
            raise PartRequiredProblem()

        accounted = self.initial_data.get("accounted") in (True, "True", "true", "1")
        verification = data.get("verification")
        if accounted and not verification:
            raise VerificationRequiredError()

        return data

    def create(self, validated_data):
        return Invoice.objects.create(file_is_original=True, **validated_data)
