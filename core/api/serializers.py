from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from expenses.models import File, Profile, Comment, Payment


class ClaimSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    description = serializers.CharField()
    amount = serializers.CharField()
    status = serializers.CharField()
    date = serializers.DateField()


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

    class Meta:
        model = Comment
        fields = ["date", "author", "content"]


@extend_schema_field(OpenApiTypes.BINARY)
class UploadField(serializers.FileField):
    pass
