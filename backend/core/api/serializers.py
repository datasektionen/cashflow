from typing import ClassVar

from rest_framework import serializers

from budget.api.serializers import PartRecommendationsMixin
from core.api.problems import NoExpensesProblem
from core.models import Claim, Comment, File, Profile


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = "__all__"


class BankInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields: ClassVar = ["bank_account", "sorting_number", "bank_name"]


class ProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name", allow_blank=False)
    last_name = serializers.CharField(source="user.last_name", allow_blank=False)
    email = serializers.EmailField(source="user.email", allow_blank=False)
    username = serializers.CharField(source="user.username", allow_blank=False)
    has_bank_info = serializers.BooleanField(
        read_only=True,
        help_text="Whether the user has registered bank account and clearing number.",
    )

    class Meta:
        model = Profile
        fields: ClassVar = [
            "id",
            "first_name",
            "last_name",
            "email",
            "username",
            "has_bank_info",
        ]


class ClaimPartSerializer(PartRecommendationsMixin, serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    cost_centre = serializers.CharField(allow_blank=True)
    secondary_cost_centre = serializers.CharField(allow_blank=True)
    budget_line = serializers.CharField(allow_blank=True)
    amount = serializers.DecimalField(max_digits=9, decimal_places=2)
    attested_by = ProfileSerializer(read_only=True)
    attest_date = serializers.DateField(read_only=True)


class ClaimTotalField(serializers.DecimalField):
    """
    Read-only claim total. Uses the `total` annotation from the viewset
    queryset when present, and falls back to summing the parts for instances
    that did not come from it (e.g. a claim that was just created).
    """

    def __init__(self, **kwargs):
        super().__init__(max_digits=10, decimal_places=2, read_only=True, **kwargs)

    def get_attribute(self, instance):
        total = getattr(instance, "total", None)
        return total if total is not None else instance.total_amount()


class ClaimSerializer(serializers.Serializer):
    """Summary of a claim for the combined claims list.

    Expects claims annotated with `total` (see `ClaimQuerySet.with_total`).
    """

    id = serializers.IntegerField(source="data_id", read_only=True)
    type = serializers.CharField()
    description = serializers.CharField()
    amount = serializers.DecimalField(
        source="total", max_digits=9, decimal_places=2, coerce_to_string=True
    )
    created_date = serializers.DateField()
    expense_date = serializers.DateField(
        source="expense_data.expense_date", allow_null=True
    )
    invoice_date = serializers.DateField(
        source="invoice_data.invoice_date", allow_null=True
    )
    is_attested = serializers.SerializerMethodField()
    is_confirmed = serializers.SerializerMethodField()
    is_paid = serializers.SerializerMethodField()
    is_flagged = serializers.SerializerMethodField(
        help_text="Whether or not this claim is flagged. Expenses only.",
    )
    voucher = serializers.SerializerMethodField(
        help_text="Fortnox voucher (verification) number. Null if not yet accounted.",
    )
    owner = ProfileSerializer(read_only=True)
    parts = ClaimPartSerializer(many=True)

    # The methods below iterate the prefetched parts rather than querying

    def get_is_attested(self, claim) -> bool:
        return all(part.attested_by_id is not None for part in claim.parts.all())

    def get_is_confirmed(self, claim) -> bool:
        return (
            claim.expense_data is not None
            and claim.expense_data.confirmed_by_id is not None
        )

    def get_is_paid(self, claim) -> bool:
        if claim.expense_data is not None:
            return claim.expense_data.reimbursement_id is not None
        return claim.invoice_data.paid_at is not None

    def get_is_flagged(self, claim) -> bool:
        if claim.expense_data is not None:
            return claim.expense_data.is_flagged
        return False

    def get_voucher(self, claim) -> str | None:
        return claim.verification or None


class CommentSerializer(serializers.ModelSerializer):
    author = ProfileSerializer(read_only=True)
    date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Comment
        fields: ClassVar = ["date", "author", "content"]


class AccountSerializer(serializers.Serializer):
    part_id = serializers.IntegerField()
    cost_centre = serializers.CharField(allow_blank=False)
    account_number = serializers.IntegerField(min_value=0, max_value=9999)


class VoucherSeriesSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=1, max_length=10, required=True)
    description = serializers.CharField(
        allow_blank=True, max_length=200, required=False, read_only=True
    )


class VoucherRowSerializer(serializers.Serializer):
    account = serializers.IntegerField(min_value=0, max_value=9999, required=True)
    # Fortnox cost centre code, e.g. "ADAALL". Optional: balancing rows
    # (e.g. crediting the liability account) are not tied to a cost centre.
    cost_centre = serializers.CharField(max_length=6, required=False)
    debit = serializers.DecimalField(
        decimal_places=2, max_digits=9, min_value=0, required=False
    )
    credit = serializers.DecimalField(
        decimal_places=2, max_digits=9, min_value=0, required=False
    )


class PendingPaymentsSerializer(serializers.Serializer):
    # Include all normal Profile fields
    owner = ProfileSerializer(source="*", read_only=True)
    # Full bank details are only exposed here: the endpoint is gated by the
    # pay permission, and the payer needs them to make the bank transfer.
    bank_info = BankInfoSerializer(source="*", read_only=True)
    total = serializers.DecimalField(max_digits=11, decimal_places=2, read_only=True)
    count = serializers.IntegerField(read_only=True)


class PaymentCreateSerializer(serializers.Serializer):
    """Request body for creating a payment: the expenses to reimburse in one go."""

    expenses = serializers.SlugRelatedField(
        slug_field="expense_data_id",
        many=True,
        allow_empty=True,
        queryset=Claim.objects.expenses(),
        help_text="IDs of the expenses to reimburse. All must belong to the same user.",
    )

    def validate_expenses(self, value):
        if not value:
            raise NoExpensesProblem()
        return value
