from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from core.api.problems import EmptyCommentProblem
from expenses.models import File, Profile, Comment, Payment


class ClaimSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    description = serializers.CharField()
    amount = serializers.CharField()
    status = serializers.CharField()
    date = serializers.DateField()
    created_date = serializers.DateField()


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


class PaymentSerializer(serializers.ModelSerializer):
    payer = ProfileSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "date", "payer"]


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
