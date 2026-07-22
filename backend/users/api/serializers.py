from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from cashflow.dauth import Permission
from core.api.serializers import BankInfoSerializer

# Helper "types" for Redoc annotation
_SCOPE_LIST = {"type": "array", "items": {"type": "string"}}
_BOOL = {"type": "boolean"}


class UserSerializer(serializers.ModelSerializer):

    permissions = serializers.SerializerMethodField()
    bank_info = BankInfoSerializer(source="profile")

    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "permissions",
            "bank_info",
        ]
        # Identity fields come from the SSO and cannot be edited here; only
        # the bank information is writable.
        read_only_fields = ["username", "first_name", "last_name", "email"]

    def update(self, user, validated_data):
        bank_info = validated_data.pop("profile", None)
        if bank_info is not None:
            for field, value in bank_info.items():
                setattr(user.profile, field, value)
            user.profile.save()
        return user

    @extend_schema_field(
        {
            "type": "object",
            "properties": {
                Permission.ATTEST.value: _SCOPE_LIST,
                Permission.ACCOUNTING.value: _SCOPE_LIST,
                Permission.VIEW_EXPENSES.value: _SCOPE_LIST,
                Permission.PAY.value: _BOOL,
                Permission.CONFIRM.value: _BOOL,
                Permission.UNCONFIRM.value: _BOOL,
                Permission.UNATTEST.value: _BOOL,
                Permission.EDIT_INVOICE.value: _BOOL,
                Permission.VIEW_ALL_PAYMENTS.value: _BOOL,
                Permission.MANAGE_FORTNOX.value: _BOOL,
            },
        }
    )
    def get_permissions(self, user):
        p = user.profile
        return {
            Permission.ATTEST: p.attestable_cost_centres(),
            Permission.ACCOUNTING: p.accountable_cost_centres(),
            Permission.VIEW_EXPENSES: p.viewable_cost_centres(),
            Permission.PAY: p.may_pay(),
            Permission.CONFIRM: p.may_confirm(),
            Permission.UNCONFIRM: p.may_unconfirm(),
            Permission.UNATTEST: p.may_unattest(),
            Permission.EDIT_INVOICE: p.may_edit_invoice(),
            Permission.VIEW_ALL_PAYMENTS: p.may_view_all_payments(),
            Permission.MANAGE_FORTNOX: p.may_manage_fortnox(),
            Permission.DELETE: p.may_delete(),
        }


class ProfilePictureQuerySerializer(serializers.Serializer):
    usernames = serializers.RegexField(
        r"^\s*[\w.@+-]+(\s*,\s*[\w.@+-]+)*\s*$",
        help_text="Comma-separated list of usernames, e.g. `hfja,turetek,marmed`",
    )

    def validate_usernames(self, value):
        names = [u.strip() for u in value.split(",")]
        if len(names) == 0:
            raise serializers.ValidationError("Usernames must not be empty")
        return names
