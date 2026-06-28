from rest_framework import serializers


class FortnoxStatusSerializer(serializers.Serializer):
    is_connected = serializers.BooleanField()
    authenticated_by = serializers.CharField(allow_null=True)
    expires_at = serializers.DateTimeField(allow_null=True)
