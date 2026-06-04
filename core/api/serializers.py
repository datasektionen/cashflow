from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from expenses.models import File, Profile


class ClaimSerializer(serializers.Serializer):
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
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")

    class Meta:
        model = Profile
        fields = [
            "id",
            "first_name",
            "last_name",
        ]


@extend_schema_field(OpenApiTypes.BINARY)
class UploadField(serializers.FileField):
    pass
