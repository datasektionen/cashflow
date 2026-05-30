from rest_framework import serializers
from rest_framework.exceptions import APIException

from expenses.models import File, Profile


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
