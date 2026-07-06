from rest_framework import serializers


class FortnoxStatusSerializer(serializers.Serializer):
    is_connected = serializers.BooleanField()
    authenticated_by = serializers.CharField(allow_null=True)
    expires_at = serializers.DateTimeField(allow_null=True)


class FortnoxAccountSerializer(serializers.Serializer):
    number = serializers.IntegerField(source="Number")
    description = serializers.CharField(source="Description")


class FortnoxCostCentreSerializer(serializers.Serializer):
    code = serializers.CharField(source="Code")
    description = serializers.CharField(source="Description")
